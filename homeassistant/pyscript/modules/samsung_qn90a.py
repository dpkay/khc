from datetime import datetime as dt
from datetime import timezone as timezone

# Communicate with the QN90A via the SamsungTV Smart integration.
QN90A_ENTITY_ID = "media_player.livingroom_qn90a"

# A mode switch takes multiple seconds to fully complete; we shouldn't interfere inbetween.
MINIMUM_NUMBER_OF_SECONDS_BETWEEN_MODE_SWITCHES = 5

REMOTE_ENTITY_ID = "remote.livingroom_qn90a"

def send_key_to_qn90a(key):
  remote.send_command(entity_id=REMOTE_ENTITY_ID, command=key)

def qn90a_enter_ambient_mode():
  send_key_to_qn90a("KEY_AMBIENT")

  # Once the mode switch completed, made the automatically-opened menu disappear again.
  task.sleep(3)
  send_key_to_qn90a("KEY_RETURN")

def qn90a_exit_ambient_mode():
  send_key_to_qn90a("KEY_EXIT")

  # Once the mode switch completed, made the automatically-opened menu disappear again.
  task.sleep(3)
  # This seems to be necessary as of 9/23/2025
  media_player.select_source(entity_id=QN90A_ENTITY_ID, source="HDMI")
  send_key_to_qn90a("KEY_RETURN")

# Note: @state_trigger for the ambient mode boolean lives in
# pyscript/samsung_qn90a_trigger.py (top-level) because pyscript
# doesn't register triggers from modules/.

def is_in_cooldown():
  # Make sure we didn't already trigger a switch recently, so we don't confuse the TV.
  ambient_mode_changed = input_boolean.livingroom_qn90a_ambient_mode.last_changed
  num_seconds_ago = (dt.now(tz=timezone.utc) - ambient_mode_changed).total_seconds()
  return num_seconds_ago < MINIMUM_NUMBER_OF_SECONDS_BETWEEN_MODE_SWITCHES

def maybe_toggle_ambient_mode():
  if not is_in_cooldown():
    # If the TV is on (most of the time), do indeed a toggle as requested.
    if is_on():
      input_boolean.livingroom_qn90a_ambient_mode.toggle()

    # If the TV is off, then turn it on but start it in ambient mode.
    else:
      log.info("TV is off. Turning on and enabling ambient mode.")
      turn_on()
      task.sleep(5)
      input_boolean.livingroom_qn90a_ambient_mode.turn_on()

def maybe_disable_ambient_mode():
  if not is_in_cooldown():
    input_boolean.livingroom_qn90a_ambient_mode.turn_off()

def maybe_enable_ambient_mode():
  if not is_in_cooldown():
    log.info("Maybe enabling ambient mode: YES")
    input_boolean.livingroom_qn90a_ambient_mode.turn_on()
  else:
    log.info("Maybe enabling ambient mode: NO")

def is_on():
  return state.get(QN90A_ENTITY_ID) == "on"

def turn_off():
  media_player.turn_off(entity_id=QN90A_ENTITY_ID)

def turn_on():
  remote.turn_on(entity_id=REMOTE_ENTITY_ID)
