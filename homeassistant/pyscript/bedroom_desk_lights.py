from datetime import datetime as dt
from datetime import timezone as timezone

DESK_LIGHT_INPUT_ENABLED_ENTITY_ID = "input_boolean.bedroom_enable_dimmer_desk_light"
DESK_LIGHT_INPUT_BRIGHTNESS_ENTITY_ID = "input_number.bedroom_windows_pc_dial_2"
DESK_LIGHT_OUTPUT_ENTITY_ID = "light.bedroom_dimmer_desk_lights_dimmer"
DESK_LIGHT_OUTPUT_MIN_SECONDS_BETWEEN_UPDATES = 0.08

# Update bedroom desk lights.
brightness_last_changed_datetime = None
@state_trigger([DESK_LIGHT_INPUT_ENABLED_ENTITY_ID,
                DESK_LIGHT_INPUT_BRIGHTNESS_ENTITY_ID])
def on_desk_light_dimmer_input_changed(var_name=None, value=None):
  # The code for this function is a bit more complicated than one would hope because our ZWave-based light
  # (output) entity can't handle the rate of updates the MIDI-based dial (input) entity produces.
  # So we need to rate limit.

  # Single update step. Queries inputs, sets light state.
  def update_light_entity():
    enabled_state = state.get(DESK_LIGHT_INPUT_ENABLED_ENTITY_ID)  # 'on' or 'off'
    brightness_in = float(state.get(DESK_LIGHT_INPUT_BRIGHTNESS_ENTITY_ID))  # 0.0 to 1.0
    brightness_out = int(brightness_in * 255)  # 0 to 100
    if enabled_state == 'on':
      light.turn_on(entity_id=DESK_LIGHT_OUTPUT_ENTITY_ID, brightness=brightness_out)
    elif enabled_state == 'off':
      light.turn_off(entity_id=DESK_LIGHT_OUTPUT_ENTITY_ID)

  # Waits for a bit, and then performs one final update step. Ensures uniqueness.
  def perform_final_update_after_delay():
    task.unique("perform_final_update_after_delay")  # Kill previous invocations.
    task.sleep(2 * DESK_LIGHT_OUTPUT_MIN_SECONDS_BETWEEN_UPDATES)
    log.info("Applying final update")
    update_light_entity()

  # Check whether this is a brightness-only change that can be skipped.
  now = dt.now(tz=timezone.utc)
  global brightness_last_changed_datetime
  if var_name == DESK_LIGHT_INPUT_BRIGHTNESS_ENTITY_ID and brightness_last_changed_datetime:
    num_seconds_ago = (now - brightness_last_changed_datetime).total_seconds()

    # If this is a redundant brightness-only change, skip, but ensure we do one last update a bit later
    # (in case this is the last change in a sequence of changes - we don't want to miss the final one).
    if num_seconds_ago < DESK_LIGHT_OUTPUT_MIN_SECONDS_BETWEEN_UPDATES:
      task.create(perform_final_update_after_delay)
      return

  brightness_last_changed_datetime = now
  update_light_entity()

