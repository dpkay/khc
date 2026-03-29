import datetime

LUCA_BED_LIGHT_ENTITY_ID = "light.bedroom_dimmer_desk_lights_dimmer"
ON_DURATION_SECONDS = 1800.0
FADEOUT_TIME_SECONDS = 240.0
MAX_BRIGHTNESS = 1.0

last_button_pressed_time = None

# Brightness should be in (0,1] for on, or falsy for off.
def set_light_brightness(brightness):
  if brightness:
    light.turn_on(entity_id=LUCA_BED_LIGHT_ENTITY_ID, brightness=brightness*255)
  else:
    light.turn_off(entity_id=LUCA_BED_LIGHT_ENTITY_ID)


def get_seconds_since_button_pressed():
  # If the button has never been pressed, return infinity.
  if not last_button_pressed_time:
    return float('inf')

  # Else, return the actual number of seconds.
  now = datetime.datetime.now()
  return (now - last_button_pressed_time).total_seconds()


def update_light_state():
  seconds_elapsed = get_seconds_since_button_pressed()

  # Take appropriate action.
  if seconds_elapsed < ON_DURATION_SECONDS:
    log.error("light on")
    set_light_brightness(MAX_BRIGHTNESS)
  elif seconds_elapsed < ON_DURATION_SECONDS + FADEOUT_TIME_SECONDS:
    log.error("light fading")
    # Fading out.
    fadeout_t = (seconds_elapsed - ON_DURATION_SECONDS) / FADEOUT_TIME_SECONDS
    set_light_brightness((1.0 - fadeout_t) * MAX_BRIGHTNESS)
  else:
    # Fadeout is done, light should be off.
    set_light_brightness(None)


def turn_on_light():
  global last_button_pressed_time
  last_button_pressed_time = datetime.datetime.now()
  update_light_state()


def turn_off_light():
  # Make it look like the button hasn't been pressed.
  global last_button_pressed_time
  last_button_pressed_time = None
  update_light_state()


def on_button_pressed():
  seconds_elapsed = get_seconds_since_button_pressed()
  if seconds_elapsed < ON_DURATION_SECONDS + FADEOUT_TIME_SECONDS:
    # If the light isn't completely dark yet, turn it off.
    turn_off_light()
  else:
    turn_on_light()


@time_trigger("period(now, 1s)")
def on_timeout_expired():
  update_light_state()
