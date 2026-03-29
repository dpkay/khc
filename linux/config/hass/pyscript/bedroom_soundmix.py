import json
import re

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


# Cache of the last published DAW params, used to only send values that actually
# changed. Without this, every MIDI fader update (~20ms) would republish all params.
last_daw_params = None

# When True, _update_daw() is suppressed. This is set during sound mix transitions
# to prevent MIDI fader jitter from re-sending output volumes while speakers are
# physically switching on/off. Without this, the continuous stream of fader updates
# from the Sparrow MIDI controller would immediately overwrite the muted state.
_muted = False


def _get_current_soundmix_name():
  candidates = []
  for name in SOUNDMIX_NAMES:
    if state.get(f"input_boolean.bedroom_sound_mix_{name}_active") == "on":
      candidates.append(name)
  if len(candidates) == 1:
    return candidates[0]
  return "none"


def _update_daw():
  # Skip during mix transitions (see _muted comment above).
  if _muted:
    return
  # Pull all values from Home Assistant control entities.
  piano_in_volume = float(input_number.bedroom_windows_pc_fader_1)
  windows_pc_in_volume = float(input_number.bedroom_windows_pc_fader_2)
  corp_laptop_in_volume = float(input_number.bedroom_windows_pc_fader_3)
  music_laptop_in_volume = float(input_number.bedroom_windows_pc_fader_4)
  speakers_out_volume = float(input_number.bedroom_windows_pc_fader_5)
  piano_reverb = float(input_number.bedroom_windows_pc_dial_1)
  headphones_out_volume = float(input_number.bedroom_windows_pc_dial_5)

  # Assemble DAW state.
  mix_name = _get_current_soundmix_name()
  new_daw_params = {
    "input_volume__piano": piano_in_volume,
    "input_volume__windows_desktop": windows_pc_in_volume,
    "input_volume__windows_laptop": corp_laptop_in_volume,
    "input_volume__external_laptop": music_laptop_in_volume,
    "input_reverb__piano": piano_reverb,
    "input_oneminusreverb__piano": 1 - piano_reverb,
    "output_volume__speakers": speakers_out_volume if mix_name in ["piano_seat_with_speakers", "desk_seat_with_speakers"] else 0,
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


def _update_plugs():
  soundmix_name = _get_current_soundmix_name()
  use_piano_seat = soundmix_name in ["piano_seat_with_speakers", "piano_seat_with_headphones"]

  service.call(domain="input_boolean",
               name="turn_on" if use_piano_seat else "turn_off",
               entity_id="input_boolean.bedroom_plug_piano_led_strip", blocking=True)
  service.call(domain="input_boolean",
               name="turn_on" if soundmix_name == "piano_seat_with_speakers" else "turn_off",
               entity_id="input_boolean.bedroom_plug_piano_speakers", blocking=True)
  service.call(domain="input_boolean",
               name="turn_on" if soundmix_name == "desk_seat_with_speakers" else "turn_off",
               entity_id="input_boolean.bedroom_plug_desk_speakers", blocking=True)


def _apply_soundmix(soundmix_name):
  """Set the active sound mix. Updates booleans, plugs, and DAW.

  The input_booleans act as radio buttons read by Stream Deck to show the active mix.
  Stream Deck calls pyscript.set_soundmix to change the active mix.
  """
  # Update booleans to reflect new mix (for Stream Deck display).
  for name in SOUNDMIX_NAMES:
    entity_id = f"input_boolean.bedroom_sound_mix_{name}_active"
    target = "on" if name == soundmix_name else "off"
    if state.get(entity_id) != target:
      state.set(entity_id, target)

  # Mute all DAW outputs before switching plugs. This prevents a burst of sound
  # through the old speakers/headphones while they're physically powering off.
  # We set _muted=True to block the continuous stream of _update_daw() calls from
  # MIDI fader jitter, which would otherwise immediately restore the output volumes.
  global last_daw_params, _muted
  _muted = True
  silence = {"output_volume__speakers": 0, "output_volume__inverted_headphones": 0, "output_volume__regular_headphones": 0}
  mqtt.publish(topic=DAW_SET_PARAMS_MQTT_TOPIC, payload=json.dumps(silence))
  last_daw_params = None  # Force _update_daw to resend all params after unmute.

  # Switch the physical plugs while muted.
  _update_plugs()

  # Wait for plugs to physically switch, then unmute and send the real volumes.
  task.sleep(1.0)
  _muted = False
  _update_daw()


@service
def set_soundmix(soundmix_name=None, entity_id=None):
  """Stream Deck calls this service to change the active sound mix."""
  if soundmix_name and soundmix_name in SOUNDMIX_NAMES:
    _apply_soundmix(soundmix_name)


@mqtt_trigger(CONTROLS_MQTT_TOPIC)
def on_bedroom_controls_received(payload_obj=None):
  # Update any changed control entities in Home Assistant.
  for control_name, value in payload_obj.items():
    entity_id = CONTROL_ENTITY_PATH_TEMPLATE.format(control_name=control_name)
    input_number.set_value(entity_id=entity_id, value=value)

  # Now update the DAW, as control values have changed.
  _update_daw()

@state_trigger(CONTROL_ENTITIES)
def on_control_entity_value_changed(var_name, value):
  _update_daw()

@service("script.turn_off_everything_in_bedroom")
def turn_off_everything_in_bedroom(entity_id=None):
  light.bedroom_ceiling_light.turn_off()
  light.bedroom_closet_light.turn_off()
  input_boolean.bedroom_plug_studio_light.turn_off()
  input_boolean.bedroom_plug_computer_monitor.turn_off()
  _apply_soundmix("none")
