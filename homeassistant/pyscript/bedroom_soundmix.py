import json
import re

DAW_SET_PARAMS_MQTT_TOPIC = "kha/bedroom/windows_pc/daw/set_params"

SOUNDMIX_NAMES = [
  "none",
  "piano_seat_with_speakers",
  "desk_seat_with_speakers",
  "piano_seat_with_headphones",
  "desk_seat_with_headphones"
]

# Stream Deck dials. Stream Deck calls input_number.set_value directly via the
# HA service API; we only react here. desk_light_brightness is consumed by
# bedroom_desk_lights.py, not the DAW, so it's not in this list.
CONTROL_ENTITIES = [
    "input_number.streamdeck_dial_master_volume",
    "input_number.streamdeck_dial_piano_volume",
    "input_number.streamdeck_dial_personal_windows_volume",
    "input_number.streamdeck_dial_personal_mac_volume",
    "input_number.streamdeck_dial_corp_mac_volume",
    "input_number.streamdeck_dial_corp_windows_volume",
]


# Cache of the last published DAW params, used to only send values that actually
# changed. Without this, every dial update would republish all params.
last_daw_params = None

# When True, _update_daw() is suppressed. This is set during sound mix transitions
# to prevent dial updates from re-sending output volumes while speakers/headphones
# are physically switching on/off. Without this, a dial update arriving mid-transition
# would immediately overwrite the muted state.
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
  master_volume = float(input_number.streamdeck_dial_master_volume)
  piano_volume = float(input_number.streamdeck_dial_piano_volume)
  personal_windows_volume = float(input_number.streamdeck_dial_personal_windows_volume)
  personal_mac_volume = float(input_number.streamdeck_dial_personal_mac_volume)
  corp_mac_volume = float(input_number.streamdeck_dial_corp_mac_volume)
  corp_windows_volume = float(input_number.streamdeck_dial_corp_windows_volume)

  # Master routes to one output based on the active mix.
  mix_name = _get_current_soundmix_name()
  uses_speakers = mix_name in ["piano_seat_with_speakers", "desk_seat_with_speakers"]
  uses_regular_headphones = mix_name == "desk_seat_with_headphones"
  uses_inverted_headphones = mix_name == "piano_seat_with_headphones"

  new_daw_params = {
    "piano_volume": piano_volume,
    "personal_windows_volume": personal_windows_volume,
    "personal_mac_volume": personal_mac_volume,
    "corp_mac_volume": corp_mac_volume,
    "corp_windows_volume": corp_windows_volume,
    "master_volume_speakers": master_volume if uses_speakers else 0,
    "master_volume_regular_headphones": master_volume if uses_regular_headphones else 0,
    # No OSC route yet — piano-seat-with-headphones currently produces silence.
    "master_volume_inverted_headphones": master_volume if uses_inverted_headphones else 0,
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
  # We set _muted=True to block any _update_daw() calls triggered by dial updates
  # arriving mid-transition, which would otherwise immediately restore the output volumes.
  global last_daw_params, _muted
  _muted = True
  silence = {"master_volume_speakers": 0, "master_volume_regular_headphones": 0, "master_volume_inverted_headphones": 0}
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
