import json
import livingroom_lights
import denon_avr
import spotify
import somfy_shades
import samsung_qn90a
import nvidia_shield_tv

@mqtt_trigger("khc/livingroom/numpad")
def on_livingroom_numpad_mqtt_received(payload_obj=None):
  # Uncomment the line below to debug incoming MQTT messages.
  log.info(payload_obj)

  # Forget about any other events (e.g. 'released') for now.
  if payload_obj['event_name'] != 'pressed':
    return

  key_name = payload_obj["key"]
  pressed_keys = payload_obj["pressed_keys"]

  if 'mod_left' in pressed_keys:
    # -----------------------
    # ALT (ZERO) MODIFIER
    # -----------------------
    # 1st number column.
    if key_name == '1_1':
      somfy_shades.send_somfy_shade_command(["livingroom_solar_left"], "up")
    elif key_name == '2_1':
      somfy_shades.send_somfy_shade_command(["livingroom_solar_left"], "stop")
    elif key_name == '3_1':
      somfy_shades.send_somfy_shade_command(["livingroom_solar_left"], "down")

    # 2nd number column.
    elif key_name == '1_2':
      somfy_shades.send_somfy_shade_command(["livingroom_solar_right"], "up")
    elif key_name == '2_2':
      somfy_shades.send_somfy_shade_command(["livingroom_solar_right"], "stop")
    elif key_name == '3_2':
      somfy_shades.send_somfy_shade_command(["livingroom_solar_right"], "down")

    # 3rd number column.
    elif key_name == '1_3':
      nvidia_shield_tv.reboot()
    elif key_name == '2_3':
      nvidia_shield_tv.match_frame_rate()
    elif key_name == '3_3':
      pass  # Unused

    # Bottom row.
    elif key_name == '4_1':
      nvidia_shield_tv.start_screensaver()
    elif key_name == '4_2':
      nvidia_shield_tv.start_kodi()
    elif key_name == '4_3':
      nvidia_shield_tv.start_youtube()

    # 4th number column.
    elif key_name == '1_4':
      samsung_qn90a.turn_off()
    elif key_name == '2_4':
      denon_avr.reset_volume_high()
    elif key_name == '3_4':
      denon_avr.reset_volume_low()

  elif 'mod_right' in pressed_keys:
    # ---------------------
    # LIGHT (ENTER) MODIFIER
    # ---------------------
    # Top row.
    if key_name == '1_1':  # OFF
      livingroom_lights.scene_all_off()
    elif key_name == '1_2':  # DIM
      livingroom_lights.scene_dim()
    elif key_name == '1_3':  # LOW
      livingroom_lights.scene_low()
    elif key_name == '1_4':
      pass  # Doesn't work on Macally numpad.

    # Second row.
    elif key_name == '2_1':  # ALL
      livingroom_lights.scene_all_on()
    elif key_name == '2_2':  # READ
      livingroom_lights.scene_livingroom_reading()
    elif key_name == '2_3':  # EAT
      livingroom_lights.scene_dining()
    elif key_name == '2_4':  # LR:ON
      livingroom_lights.scene_on_livingroom_only()

    # Third row.
    elif key_name == '3_1':
      pass
    elif key_name == '3_2':
      pass
    elif key_name == '3_3':
      pass
    elif key_name == '3_4':  # LR:OFF
      livingroom_lights.scene_dim_livingroom_only()

    # Bottom row.
    elif key_name == '4_1':
      pass
    elif key_name == '4_2':
      pass
    elif key_name == '4_3':
      pass

  elif 'mod_center' in pressed_keys:
    # --------------------
    # MUSIC (DOT) MODIFIER
    # --------------------
    if key_name == '1_1':
      spotify.play(1)
    if key_name == '1_2':
      spotify.play(2)
    if key_name == '1_3':
      spotify.play(3)
    if key_name == '1_4':
      spotify.play(4)
    if key_name == '2_1':
      spotify.play(5)
    if key_name == '2_2':
      spotify.play(6)
    if key_name == '2_3':
      spotify.play(7)
    if key_name == '2_4':
      spotify.play(8)
    if key_name == '3_1':
      spotify.play(9)
    if key_name == '3_2':
      spotify.play(10)
    if key_name == '3_3':
      spotify.play(11)
    if key_name == '3_4':
      spotify.play(12)
    if key_name == '4_1':
      spotify.play(13)
    if key_name == '4_2':
      spotify.play(14)
    if key_name == '4_3':
      spotify.play(15)

  else:
    # ------------
    # NO MODIFIERS
    # ------------
    # Bottom right column: Volume control.
    if key_name == '2_4':
      denon_avr.increase_volume()
    elif key_name == '3_4':
      denon_avr.decrease_volume()

    # Top row: Media player.
    elif key_name == '1_1':
      nvidia_shield_tv.previous_track()
    elif key_name == '1_2':
      nvidia_shield_tv.play_pause()
    elif key_name == '1_3':
      nvidia_shield_tv.next_track()
    elif key_name == '1_4':
      samsung_qn90a.maybe_toggle_ambient_mode()

    # Center block: NVidia Shield.
    elif key_name == '2_1':
      pass  # Unused
    elif key_name == '2_2':
      nvidia_shield_tv.send_key("up")
    elif key_name == '2_3':
      nvidia_shield_tv.menu()
    elif key_name == '3_1':
      nvidia_shield_tv.send_key("left")
    elif key_name == '3_2':
      nvidia_shield_tv.send_key("center")
    elif key_name == '3_3':
      nvidia_shield_tv.send_key("right")
    elif key_name == '4_1':
      nvidia_shield_tv.send_key("back")
    elif key_name == '4_2':
      nvidia_shield_tv.send_key("down")
    elif key_name == '4_3':
      nvidia_shield_tv.send_key("home")

