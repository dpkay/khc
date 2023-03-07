# Synchronizes entities on the left side of this map with the right side of this map.
entity_map = {
    "input_boolean.livingroom_plug_xmas_lights": "switch.khc_tasmota_001_sonoff_s31lite",
    "input_boolean.diningroom_plug_xmas_lights": "switch.khc_tasmota_002_sonoff_s31lite",
    "input_boolean.bedroom_plug_piano_speakers": "switch.khc_tasmota_003_sonoff_s31lite",
    "input_boolean.bedroom_plug_piano_led_strip": "switch.khc_tasmota_004_sonoff_s31lite",
    "input_boolean.bedroom_plug_computer_monitor": "switch.khc_tasmota_005_sonoff_s31",
    "input_boolean.bedroom_plug_studio_light": "switch.khc_tasmota_006_sonoff_s31",
    "input_boolean.bedroom_plug_desk_speakers": "switch.khc_tasmota_007_sonoff_s31",
    # "UNUSED": "switch.khc_tasmota_008_sonoff_s31",
    "input_boolean.livingroom_plug_nvidia_shield": "switch.khc_tasmota_009_sonoff_s31",
}


@task_unique("on_entity_map_lhs_changed", kill_me=True)
@state_trigger(list(entity_map.keys()))
def on_entity_map_lhs_changed(var_name=None, value=None):
    target_entity_id = entity_map[var_name]
    service.call(
        domain="switch", name=f"turn_{value}", entity_id=target_entity_id, blocking=True
    )
