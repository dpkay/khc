import json

# The topic is as follows, per https://zwave-js.github.io/zwave-js-ui/#/guide/mqtt.
ZWAVE_WRITE_VALUE_MQTT_TOPIC = "zwave/_CLIENTS/ZWAVE_GATEWAY-zwave-js-ui/api/writeValue/set"

# Node IDs as set up in the zwave-js-ui web interface (accessible at localhost:8091)
ZWAVE_NODE_ID_BY_SHADE_NAME = {
  "livingroom_solar_right": 3,
  "livingroom_solar_left": 4,
  "kidsroom_blackout_left": 5,
  "kidsroom_blackout_right": 6,
  "kidsroom_solar_left": 7,
  "kidsroom_solar_right": 8,
  "bedroom_blackout_left": 9,
  "bedroom_blackout_right": 10,
  "bedroom_solar_left": 11,
  "bedroom_solar_right": 12,
}

def zwave_write_value(value_id, value, options):
  # Communicate with zwave-js-ui (which needs to be running as a service).
  payload = {"args": [value_id, value, options]}
  mqtt.publish(topic=ZWAVE_WRITE_VALUE_MQTT_TOPIC, payload=json.dumps(payload))

def call_command(node_id, command):
  if command == "up":
    zwave_property = "Down"  # 'Up' and 'Down' are inverted here for whatever reason.
    zwave_value = True
  elif command == "down":
    zwave_property = "Up"  # 'Up' and 'Down' are inverted here for whatever reason.
    zwave_value = True
  elif command == "stop":
    zwave_property = "Up"  # Doesn't matter whether up or down, we're stopping anyway.
    zwave_value = False
  else:
    raise ValueError(f"Unknown command: {command}")

  zwave_write_value(
    value_id={
      "nodeId": node_id,
      "commandClass": 38,
      "endpoint": 0,
      "property": zwave_property
    },
    value=zwave_value,
    options={}
  )