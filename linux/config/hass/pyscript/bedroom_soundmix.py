import json
import re
import tasmota

DAW_SET_PARAMS_MQTT_TOPIC = "kha/bedroom/windows_pc/daw/set_params"
CONTROLS_MQTT_TOPIC = "kha/bedroom/windows_pc/controls"
CONTROL_ENTITY_PATH_TEMPLATE = "input_number.bedroom_windows_pc_{control_name}"

SOUNDMIX_NAMES = [
  "none",
  "piano_seat_with_speakers",
  "desk_seat_with_speakers",
  "piano_seat_with_headphones",
  "desk_seat_with_headphones"
]

CONTROL_ENTITIES = [
    "input_number.bedroom_windows_pc_fader_1",
    "input_number.bedroom_windows_pc_fader_2",
    "input_number.bedroom_windows_pc_fader_3",
    "input_number.bedroom_windows_pc_fader_4",
    "input_number.bedroom_windows_pc_fader_5",
    "input_number.bedroom_windows_pc_dial_1",
    "input_number.bedroom_windows_pc_dial_2",
    "input_number.bedroom_windows_pc_dial_3",
    "input_number.bedroom_windows_pc_dial_4",
    "input_number.bedroom_windows_pc_dial_5",
]


# Global variable, used in the update_daw function.
last_daw_params = None


def get_current_soundmix_name():
  candidates = []
  for name in SOUNDMIX_NAMES:
    if state.get(f"input_boolean.bedroom_sound_mix_{name}_active") == "on":
      candidates.append(name)
  if len(candidates) == 1:
    return candidates[0]
  return "none"


def update_daw():
  # Pull all values from Home Assistant control entities.
  piano_in_volume = float(input_number.bedroom_windows_pc_fader_1)
  windows_pc_in_volume = float(input_number.bedroom_windows_pc_fader_2)
  corp_laptop_in_volume = float(input_number.bedroom_windows_pc_fader_3)
  music_laptop_in_volume = float(input_number.bedroom_windows_pc_fader_4)
  speakers_out_volume = float(input_number.bedroom_windows_pc_fader_5)
  piano_reverb = float(input_number.bedroom_windows_pc_dial_1)
  headphones_out_volume = float(input_number.bedroom_windows_pc_dial_5)

  # Assemble DAW state.
  mix_name = get_current_soundmix_name()
  new_daw_params = {
    "input_volume__piano": piano_in_volume,
    "input_volume__windows_desktop": windows_pc_in_volume,
    "input_volume__windows_laptop": corp_laptop_in_volume,
    "input_volume__external_laptop": music_laptop_in_volume,
    "input_reverb__piano": piano_reverb,
    "input_oneminusreverb__piano": 1 - piano_reverb,
    "output_volume__piano_speakers": speakers_out_volume if mix_name == "piano_seat_with_speakers" else 0,
    "output_volume__desk_speakers": speakers_out_volume if mix_name == "desk_seat_with_speakers" else 0,
    "output_volume__inverted_headphones": headphones_out_volume if mix_name == "piano_seat_with_headphones" else 0,
    "output_volume__regular_headphones": headphones_out_volume if mix_name == "desk_seat_with_headphones" else 0
  }

  # Assemble list of parameters ("publishable_daw_params") that changed since last time.
  global last_daw_params
  if last_daw_params:
    publishable_daw_params = {}
    for key, value in new_daw_params.items():
      if (not key in last_daw_params) or (last_daw_params[key] != value):
        publishable_daw_params[key] = value
  else:
    publishable_daw_params = new_daw_params

  # Send list of changed parameters to DAW.
  if publishable_daw_params:
    mqtt.publish(topic=DAW_SET_PARAMS_MQTT_TOPIC, payload=json.dumps(publishable_daw_params))

  # Backup current parameters for comparison in the next cycle.
  last_daw_params = new_daw_params


def update_plugs():
  soundmix_name = get_current_soundmix_name()
  use_piano_seat = soundmix_name in ["piano_seat_with_speakers", "piano_seat_with_headphones"]

  state.set("input_boolean.bedroom_plug_piano_led_strip",
            "on" if use_piano_seat else "off")
  state.set("input_boolean.bedroom_plug_piano_speakers",
            "on" if soundmix_name == "piano_seat_with_speakers" else "off")
  state.set("input_boolean.bedroom_plug_desk_speakers",
            "on" if soundmix_name == "desk_seat_with_speakers" else "off")


@task_unique("on_soundmix_input_boolean_changed", kill_me=True)
@state_trigger([f"input_boolean.bedroom_sound_mix_{name}_active" for name in SOUNDMIX_NAMES])
def on_soundmix_input_boolean_changed(trigger_type=None, var_name=None, value=None, old_value=None):
  # User turned the input_boolean off. That's not supported. Just turn it back on.
  if value == 'off':
    service.call(domain="input_boolean", name="turn_on", entity_id=var_name)
    return

  # User turned the input_boolean on. Determine the corresponding soundmix name.
  matches = re.match(r"input_boolean.bedroom_sound_mix_(.*)_active", var_name)
  soundmix_name = matches[1]

  # Now update all the input_booleans. We must enable both the "blocking" attribute
  # in the call here, as well as @task_unique on the function, in order to avoid recursive calls.
  for name in SOUNDMIX_NAMES:
    service.call(
      domain="input_boolean",
      name="turn_on" if soundmix_name == name else "turn_off",
      entity_id=f"input_boolean.bedroom_sound_mix_{name}_active",
      blocking=True)

  # Now update both the DAW and the plugs since the sound mix has changed.
  update_daw()
  update_plugs()


@mqtt_trigger(CONTROLS_MQTT_TOPIC)
def on_bedroom_controls_received(payload_obj=None):
  # Update any changed control entities in Home Assistant.
  for control_name, value in payload_obj.items():
    entity_id = CONTROL_ENTITY_PATH_TEMPLATE.format(control_name=control_name)
    input_number.set_value(entity_id=entity_id, value=value)

  # Now update the DAW, as control values have changed.
  update_daw()

# TODO: maybe delete this with real faders
@state_trigger(CONTROL_ENTITIES)
def on_control_entity_value_changed(var_name, value):
  update_daw()
  #log.info(f"{var_name=} {value=}")

@service("script.turn_off_everything_in_bedroom")
def turn_off_everything_in_bedroom(entity_id=None):
  light.bedroom_ceiling_light.turn_off()
  light.bedroom_closet_light.turn_off()
  #input_boolean.bedroom_plug_desk_light.turn_off()
  input_boolean.bedroom_plug_studio_light.turn_off()
  input_boolean.bedroom_plug_computer_monitor.turn_off()
  input_boolean.bedroom_sound_mix_none_active.turn_on()


