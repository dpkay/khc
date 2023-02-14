#!/usr/bin/python3

from key_codes import *
from pairing import PairingSocket
from sending_keys import SendingKeySocket
import json
import os
import paho.mqtt.client
import sys
import time


MQTT_CLIENT_NAME = "mqtt_to_shield"
MQTT_TOPIC_PREFIX = "kha/livingroom/shield"

# Set your server name, server ip and client name here
SERVER_NAME = "Nvidia Shield"
SERVER_IP = '192.168.1.218'
CLIENT_NAME = "mqtt_to_shield"

def send_shield_key(name):
  # unfortunately can't send menu key
  # https://www.reddit.com/r/ShieldAndroidTV/comments/ih81m1/adb_and_keyevent_for_menu_button/
  if name == 'down':
    sending_key_socket.send_key_command(KEYCODE_DPAD_DOWN)
  elif name == 'up':
    sending_key_socket.send_key_command(KEYCODE_DPAD_UP)
  elif name == 'right':
    sending_key_socket.send_key_command(KEYCODE_DPAD_RIGHT)
  elif name == 'left':
    sending_key_socket.send_key_command(KEYCODE_DPAD_LEFT)
  elif name == 'center':
    sending_key_socket.send_key_command(KEYCODE_DPAD_CENTER)
  elif name == 'home':
    sending_key_socket.send_key_command(KEYCODE_HOME)
  elif name == 'back':
    sending_key_socket.send_key_command(KEYCODE_BACK)
  elif name == 'play_pause':
    sending_key_socket.send_key_command(KEYCODE_MEDIA_PLAY_PAUSE)

def on_connect(client, userdata, flags, rc):
    print("Connected with result code {0}".format(str(rc)))
    client.subscribe(f"{MQTT_TOPIC_PREFIX}/#")

def on_message(client, userdata, msg):
    # Decode payload.
    payload_decoded = msg.payload.decode("utf-8", "ignore")
    try:
        payload_json = json.loads(payload_decoded)
    except Exception as e:
        print(f"Unable to decode payload '{payload_decoded}':", e)
        return

    # Uncomment the following for debugging the received payload.
    print(json.dumps(payload_json, indent=2))

    # Now act based on the topic name.
    if msg.topic == f"{MQTT_TOPIC_PREFIX}/press_key":
        try:
            key_name = payload_json['name']
        except KeyError as e:
            print(f"Unable to obtain mix name from payload:", e)
            return

        send_shield_key(key_name)

if __name__ == "__main__":
  # if argument for pairing exist, start to pair
  if len(sys.argv) > 1 and sys.argv[1] == "pairing":
      pairing_sock = PairingSocket(CLIENT_NAME, SERVER_IP)
      pairing_sock.connect()
      pairing_sock.start_pairing()
      assert (pairing_sock.connected),"Connection unsuccessful!"

  # Set up MQTT.
  while True:
    try:
      print("Attempting to connect to MQTT server...")
      mqtt_client = paho.mqtt.client.Client(MQTT_CLIENT_NAME)
      mqtt_client.on_connect = on_connect  # Define callback function for successful connection
      mqtt_client.on_message = on_message  # Define callback function for receipt of a message
      mqtt_client.connect('127.0.0.1', 1883)
      mqtt_client.username_pw_set(os.environ["MQTT_USER"],
                                  os.environ["MQTT_PASSWORD"])

      sending_key_socket = SendingKeySocket(SERVER_NAME, SERVER_IP)
      sending_key_socket.connect(keyfile_path="/home/dpkay/key.pem", certfile_path="/home/dpkay/cert.pem")
      mqtt_client.loop_forever()  # Start networking daemon

    except Exception as e:
      print("Error:", e)
      print("Retrying in 1 second.")
      time.sleep(1)

