# BEDROOM
# light.bedroom_ceiling_light
# light.bedroom_closet_light

# KIDSROOM
# light.luca_bedroom_cove_lights
# light.luca_bedroom_main_lights

# BATHROOM
# light.main_bathroom_main_lights

# DINING/LIVING/KITCHEN ("living area")
# light.dining_room_chandelier
# light.dining_room_cove_lights
# light.front_foyer_main_lights
# light.hallway_main_lights
# light.kitchen_main_lights
# light.kitchen_under_cabinet
# light.living_room_cove_lights
# light.living_room_main_lights
# light.living_room_sconces

def scene_all_on():
  # ON
  light.front_foyer_main_lights.turn_on()
  light.hallway_main_lights.turn_on()
  light.kitchen_main_lights.turn_on()
  light.kitchen_under_cabinet.turn_on()
  light.living_room_main_lights.turn_on()
  light.living_room_cove_lights.turn_on()
  light.living_room_sconces.turn_on()
  light.dining_room_cove_lights.turn_on()
  light.dining_room_chandelier.turn_on()
  input_boolean.livingroom_plug_xmas_lights.turn_on()
  input_boolean.diningroom_plug_xmas_lights.turn_on()

def scene_livingroom_reading():
  # ON
  light.living_room_main_lights.turn_on()
  light.living_room_cove_lights.turn_on()
  light.living_room_sconces.turn_on()
  input_boolean.livingroom_plug_xmas_lights.turn_on()

  # OFF
  light.front_foyer_main_lights.turn_off()
  light.hallway_main_lights.turn_off()
  light.kitchen_main_lights.turn_off()
  light.kitchen_under_cabinet.turn_off()
  light.dining_room_cove_lights.turn_off()
  light.dining_room_chandelier.turn_off()
  light.living_room_sconces.turn_off()
  input_boolean.diningroom_plug_xmas_lights.turn_off()

def scene_dining():
  # ON
  light.dining_room_cove_lights.turn_on()
  light.dining_room_chandelier.turn_on()
  input_boolean.diningroom_plug_xmas_lights.turn_on()

  # OFF
  light.living_room_main_lights.turn_off()
  light.living_room_cove_lights.turn_off()
  light.living_room_sconces.turn_off()
  light.front_foyer_main_lights.turn_off()
  light.hallway_main_lights.turn_off()
  light.kitchen_main_lights.turn_off()
  light.kitchen_under_cabinet.turn_off()
  light.living_room_sconces.turn_off()
  input_boolean.livingroom_plug_xmas_lights.turn_off()

def scene_all_off():
  # OFF
  light.front_foyer_main_lights.turn_off()
  light.hallway_main_lights.turn_off()
  light.kitchen_main_lights.turn_off()
  light.kitchen_under_cabinet.turn_off()
  light.living_room_main_lights.turn_off()
  light.living_room_cove_lights.turn_off()
  light.living_room_sconces.turn_off()
  light.dining_room_cove_lights.turn_off()
  light.dining_room_chandelier.turn_off()
  input_boolean.diningroom_plug_xmas_lights.turn_off()
  input_boolean.livingroom_plug_xmas_lights.turn_off()

def scene_dim():
  # ON
  light.living_room_sconces.turn_on(brightness=70)
  input_boolean.livingroom_plug_xmas_lights.turn_on()

  # OFF
  light.front_foyer_main_lights.turn_off()
  light.hallway_main_lights.turn_off()
  light.kitchen_main_lights.turn_off()
  light.kitchen_under_cabinet.turn_off()
  light.living_room_main_lights.turn_off()
  light.living_room_cove_lights.turn_off()
  light.living_room_sconces.turn_off()
  light.dining_room_cove_lights.turn_off()
  light.dining_room_chandelier.turn_off()
  input_boolean.diningroom_plug_xmas_lights.turn_off()

def scene_low():
  # ON
  light.dining_room_cove_lights.turn_on(brightness=30)
  light.living_room_cove_lights.turn_on(brightness=30)
  light.living_room_main_lights.turn_on(brightness=3)
  light.living_room_sconces.turn_on(brightness=90)
  input_boolean.diningroom_plug_xmas_lights.turn_on()
  input_boolean.livingroom_plug_xmas_lights.turn_on()

  # OFF
  light.front_foyer_main_lights.turn_off()
  light.hallway_main_lights.turn_off()
  light.kitchen_main_lights.turn_off()
  light.kitchen_under_cabinet.turn_off()
  light.dining_room_cove_lights.turn_off()
  light.dining_room_chandelier.turn_off()

def scene_dim_livingroom_only():
  # ON
  input_boolean.livingroom_plug_xmas_lights.turn_on()

  # OFF
  light.front_foyer_main_lights.turn_off()
  light.hallway_main_lights.turn_off()
  light.living_room_main_lights.turn_off()
  light.living_room_cove_lights.turn_off()
  light.living_room_sconces.turn_off()
  light.dining_room_cove_lights.turn_off()
  input_boolean.diningroom_plug_xmas_lights.turn_off()

def scene_on_livingroom_only():
  # ON
  light.living_room_main_lights.turn_on(brightness=70)
  light.living_room_cove_lights.turn_on()
  light.dining_room_cove_lights.turn_on()
  input_boolean.livingroom_plug_xmas_lights.turn_on()
