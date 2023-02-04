import json
import re

DAW_SET_PARAMS_MQTT_TOPIC = "kha/bedroom/windows_pc/daw/set_params"
FADERS_MQTT_TOPIC = "kha/bedroom/windows_pc/faders"
FADER_ENTITY_PATH_TEMPLATE = "input_number.bedroom_windows_pc_fader_{n}"

SOUNDMIX_NAMES = [
  "none",
  "piano_seat_with_speakers",
  "desk_seat_with_speakers",
  "piano_seat_with_headphones",
  "desk_seat_with_headphones"
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
  # Pull all values from Home Assistant fader entities.
  master_volume = float(input_number.bedroom_windows_pc_fader_1)
  piano_volume = float(input_number.bedroom_windows_pc_fader_2)
  windows_desktop_volume = float(input_number.bedroom_windows_pc_fader_3)
  windows_laptop_volume = float(input_number.bedroom_windows_pc_fader_4)
  external_laptop_volume = float(input_number.bedroom_windows_pc_fader_5)

  # Assemble DAW state.
  mix_name = get_current_soundmix_name()
  new_daw_params = {
    "input__piano": piano_volume,
    "input__windows_desktop": windows_desktop_volume,
    "input__windows_laptop": windows_laptop_volume,
    "input__external_laptop": external_laptop_volume,
    "output__piano_speakers": master_volume if mix_name == "piano_seat_with_speakers" else 0,
    "output__desk_speakers": master_volume if mix_name == "desk_seat_with_speakers" else 0,
    "output__inverted_headphones": master_volume if mix_name == "piano_seat_with_headphones" else 0,
    "output__regular_headphones": master_volume if mix_name == "desk_seat_with_headphones" else 0
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
  service.call(domain="light",
               entity_id="light.bedroom_plug_piano_led_strip",
               name=f"turn_{'on' if use_piano_seat else 'off'}")
  service.call(domain="light",
               entity_id="light.bedroom_plug_piano_speakers",
               name=f"turn_{'on' if soundmix_name == 'piano_seat_with_speakers' else 'off'}")
  service.call(domain="light",
               entity_id="light.bedroom_plug_desk_speakers",
               name=f"turn_{'on' if soundmix_name == 'desk_seat_with_speakers' else 'off'}")


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


@mqtt_trigger(FADERS_MQTT_TOPIC)
def on_bedroom_faders_received(payload_obj=None):
  # Update any changed fader entities in Home Assistant.
  for name, value in payload_obj.items():
    entity_id = FADER_ENTITY_PATH_TEMPLATE.format(n=name)
    input_number.set_value(entity_id=entity_id, value=value)

  # Now update the DAW, as fader values have changed.
  update_daw()
