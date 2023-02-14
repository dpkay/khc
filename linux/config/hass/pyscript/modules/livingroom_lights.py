import tasmota
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

def toggle_bathroom():
  light.main_bathroom_main_lights.toggle()

def livingarea_all_on():
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
  switch.turn_on(entity_id=tasmota.SWITCH_LIVINGROOM_XMAS_LIGHTS_ENTITY_ID)
  switch.turn_on(entity_id=tasmota.SWITCH_DININGROOM_XMAS_LIGHTS_ENTITY_ID)

def scene_livingroom_reading():
  # ON
  light.living_room_main_lights.turn_on()
  light.living_room_cove_lights.turn_on()
  light.living_room_sconces.turn_on()
  switch.turn_on(entity_id=tasmota.SWITCH_LIVINGROOM_XMAS_LIGHTS_ENTITY_ID)

  # OFF
  light.front_foyer_main_lights.turn_off()
  light.hallway_main_lights.turn_off()
  light.kitchen_main_lights.turn_off()
  light.kitchen_under_cabinet.turn_off()
  light.dining_room_cove_lights.turn_off()
  light.dining_room_chandelier.turn_off()
  light.living_room_sconces.turn_off()
  switch.turn_off(entity_id=tasmota.SWITCH_DININGROOM_XMAS_LIGHTS_ENTITY_ID)

def scene_dining():
  # ON
  light.dining_room_cove_lights.turn_on()
  light.dining_room_chandelier.turn_on()
  switch.turn_on(entity_id=tasmota.SWITCH_DININGROOM_XMAS_LIGHTS_ENTITY_ID)

  # OFF
  light.living_room_main_lights.turn_off()
  light.living_room_cove_lights.turn_off()
  light.living_room_sconces.turn_off()
  light.front_foyer_main_lights.turn_off()
  light.hallway_main_lights.turn_off()
  light.kitchen_main_lights.turn_off()
  light.kitchen_under_cabinet.turn_off()
  light.living_room_sconces.turn_off()
  switch.turn_off(entity_id=tasmota.SWITCH_LIVINGROOM_XMAS_LIGHTS_ENTITY_ID)

def scene_very_off():
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
  switch.turn_off(entity_id=tasmota.SWITCH_LIVINGROOM_XMAS_LIGHTS_ENTITY_ID)
  switch.turn_off(entity_id=tasmota.SWITCH_DININGROOM_XMAS_LIGHTS_ENTITY_ID)

def scene_dim():
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
  switch.turn_off(entity_id=tasmota.SWITCH_DININGROOM_XMAS_LIGHTS_ENTITY_ID)

  # ON
  light.living_room_sconces.turn_on(brightness=70)
  switch.turn_on(entity_id=tasmota.SWITCH_LIVINGROOM_XMAS_LIGHTS_ENTITY_ID)

def scene_dim2():
  # OFF
  light.front_foyer_main_lights.turn_off()
  light.hallway_main_lights.turn_off()
  light.kitchen_main_lights.turn_off()
  light.kitchen_under_cabinet.turn_off()
  light.dining_room_cove_lights.turn_off()
  light.dining_room_chandelier.turn_off()

  # ON
  light.dining_room_cove_lights.turn_on(brightness=30)
  light.living_room_cove_lights.turn_on(brightness=30)
  light.living_room_main_lights.turn_on(brightness=3)
  light.living_room_sconces.turn_on(brightness=90)
  switch.turn_on(entity_id=tasmota.SWITCH_DININGROOM_XMAS_LIGHTS_ENTITY_ID)
  switch.turn_on(entity_id=tasmota.SWITCH_LIVINGROOM_XMAS_LIGHTS_ENTITY_ID)

def scene_dim_livingroom_only():
  light.front_foyer_main_lights.turn_off()
  light.hallway_main_lights.turn_off()
  light.living_room_main_lights.turn_off()
  light.living_room_cove_lights.turn_off()
  light.living_room_sconces.turn_off()
  light.dining_room_cove_lights.turn_off()
  switch.turn_off(entity_id=tasmota.SWITCH_DININGROOM_XMAS_LIGHTS_ENTITY_ID)
  switch.turn_on(entity_id=tasmota.SWITCH_LIVINGROOM_XMAS_LIGHTS_ENTITY_ID)

def scene_on_livingroom_only():
  light.living_room_main_lights.turn_on(brightness=70)
  light.living_room_cove_lights.turn_on()
  light.dining_room_cove_lights.turn_on()
  switch.turn_on(entity_id=tasmota.SWITCH_LIVINGROOM_XMAS_LIGHTS_ENTITY_ID)
