import json
import livingroom_lights
import denon_avr
import somfy_shades
import samsung_qn90a
import nvidia_shield_tv

@service("script.send_somfy_shade_command")
def send_somfy_shade_command(shade_names=None, command=None, entity_id=None):
  try:
    node_ids = [somfy_shades.ZWAVE_NODE_ID_BY_SHADE_NAME[name] for name in shade_names]
  except KeyError as e:
    raise ValueError(f"Unknown shade name: ", e)

  for node_id in node_ids:
    somfy_shades.call_command(node_id, command)

@mqtt_trigger("khc/livingroom/numpad")
def on_livingroom_numpad_mqtt_received(payload_obj=None):
  #log.info("RECEIVED")
  #log.info(payload_obj)
  if payload_obj['event_name'] != 'pressed':
    return
  key_name = payload_obj["key"]

  # TV control.
  #if key_name == "backspace":
  # Bottom row: TV control.
  if key_name == "zero":
    samsung_qn90a.maybe_toggle_qn90a_ambient_mode()
  elif key_name == "dot":
    pass  # Unused.


  # Bottom right column: Volume control.
  elif key_name == "minus":
    denon_avr.reset_volume()
  elif key_name == "plus":
    denon_avr.increase_volume()
  elif key_name == "enter":
    denon_avr.decrease_volume()

  # Top row: Lights.
  elif key_name == "backspace":
    pass  # Unused.
  elif key_name == "equals":
    pass  # Unused.
  elif key_name == "slash":
    livingroom_lights.scene_dim()
  elif key_name == "asterisk":
    livingroom_lights.scene_off()

  # Center block: NVidia Shield.
  elif key_name == "seven":
    nvidia_shield_tv.reboot()
  elif key_name == "eight":
    nvidia_shield_tv.send_key("up")
  elif key_name == "nine":
    pass  # Unused.
  elif key_name == "four":
    nvidia_shield_tv.send_key("left")
  elif key_name == "five":
    nvidia_shield_tv.send_key("center")
  elif key_name == "six":
    nvidia_shield_tv.send_key("right")
  elif key_name == "one":
    nvidia_shield_tv.send_key("back")
  elif key_name == "two":
    nvidia_shield_tv.send_key("down")
  elif key_name == "three":
    nvidia_shield_tv.send_key("home")

  """
  elif key_name == "two":
    nvidia_shield_tv.send_key("down")
  elif key_name == "five":
    nvidia_shield_tv.send_key("up")
  elif key_name == "one":
    nvidia_shield_tv.send_key("left")
  elif key_name == "three":
    nvidia_shield_tv.send_key("right")
  elif key_name == "zero":
    nvidia_shield_tv.send_key("center")
  elif key_name == "dot":
    nvidia_shield_tv.send_key("back")
  elif key_name == "four":
    nvidia_shield_tv.send_key("home")
  elif key_name == "seven":
    nvidia_shield_tv.send_key("play_pause")
  """

