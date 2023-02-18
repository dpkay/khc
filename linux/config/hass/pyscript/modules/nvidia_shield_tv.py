import json
import samsung_qn90a
import denon_avr

CAST_ENTITY_ID = "media_player.shield_cast"
ANDROIDTV_ENTITY_ID = "media_player.shield_androidtv"

def _adb_shell_command(command):
  androidtv.adb_command(entity_id=ANDROIDTV_ENTITY_ID, command=command)

def send_key(name):
  # Send a message to the Shield MQTT service.
  SHIELD_MQTT_TOPIC = "kha/livingroom/shield/press_key"
  payload = f'{{"name": "{name}"}}'
  mqtt.publish(topic=SHIELD_MQTT_TOPIC, payload=payload)

def reboot():
  # Power cycle the plug which the Shield is plugged into.
  light.livingroom_plug_nvidia_shield.turn_off()
  task.sleep(2)
  light.livingroom_plug_nvidia_shield.turn_on()

def play_pause():
  media_player.media_play_pause(entity_id=CAST_ENTITY_ID)

def previous_track():
  media_player.media_previous_track(entity_id=CAST_ENTITY_ID)

def next_track():
  media_player.media_next_track(entity_id=CAST_ENTITY_ID)

def menu():
  _adb_shell_command("am start -a android.settings.SETTINGS")

def start_screensaver():
  _adb_shell_command("am start -n com.android.systemui/.Somnambulator")
  samsung_qn90a.maybe_disable_ambient_mode()

def start_kodi():
  # Need to kill screensaver manual if active. But the following doesn't work:
  #     _adb_shell_command("am force-stop com.android.systemui")
  #
  # So, have to resort to a hack.
  send_key("home")
  task.sleep(0.5)

  # Now start Kodi.
  _adb_shell_command("am start -n org.xbmc.kodi/.Splash")
  samsung_qn90a.maybe_disable_ambient_mode()

def start_youtube():
  # See comment in start_kodi.
  send_key("home")
  task.sleep(0.5)
  _adb_shell_command("am start -n com.google.android.youtube.tv/com.google.android.apps.youtube.tv.activity.ShellActivity")
  samsung_qn90a.maybe_disable_ambient_mode()

# Make sure the TV is on and in ambient mode if someone casts a music source.
# And ambient mode off otherwise.
@state_trigger(f"{CAST_ENTITY_ID}.app_name")
def on_cast_app_name_changed(value=None):
  try:
    app_name = state.get(f"{CAST_ENTITY_ID}.app_name").strip().lower()
    log.info(f"Cast app name changed to: '{app_name}'")
    if app_name in ["spotify", "youtube music", "google play music"]:
      samsung_qn90a.maybe_enable_ambient_mode()
    else:
      samsung_qn90a.maybe_disable_ambient_mode()
  except AttributeError:
    pass

@state_trigger(f"{CAST_ENTITY_ID}")
def on_cast_something_changed(trigger_type=None, var_name=None, value=None, old_value=None):
  log.info(f"{trigger_type=} {var_name=} {value=} {old_value=}")
