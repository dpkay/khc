import json

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
