def scene_off():
  # OFF
  light.living_room_main_lights.turn_off()
  light.living_room_cove_lights.turn_off()
  light.dining_room_cove_lights.turn_off()
  light.dining_room_chandelier.turn_off()
  light.living_room_cove_lights.turn_off()
  light.living_room_sconces.turn_off()
  light.livingroom_plug_xmas_lights.turn_off()

def scene_dim():
  # OFF
  light.living_room_main_lights.turn_off()
  light.living_room_cove_lights.turn_off()
  light.dining_room_cove_lights.turn_off()
  light.dining_room_chandelier.turn_off()
  light.living_room_cove_lights.turn_off()

  # ON
  light.living_room_sconces.turn_on(brightness=70)
  light.livingroom_plug_xmas_lights.turn_on()
