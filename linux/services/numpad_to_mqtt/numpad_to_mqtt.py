#!/usr/bin/python3

import json
import numpy
import os
import paho.mqtt.client
import pygame
import sys
import time

MQTT_CLIENT_NAME = "numpad_to_mqtt"
MQTT_TOPIC = "khc/livingroom/numpad"
MACALLY_RFNUMKEY_KEY_LIST = [
    # [name, event.key, event.scancode]
    # name is of the form <row>_<column>
    ['1_1', 8, 22],  # backspace
    ['1_2', 61, 21],  # equals
    ['1_3', 267, 106],  # slash
    ['1_4', 268, 63],  # asterisk
    ['2_1', 263, 79],  # seven
    ['2_2', 264, 80],  # eight
    ['2_3', 265, 81],  # nine
    ['2_4', 269, 82],  # minus
    ['3_1', 260, 83],  # four
    ['3_2', 261, 84],  # five
    ['3_3', 262, 85],  # six
    ['3_4', 270, 86],  # plus
    ['4_1', 257, 87],  # one
    ['4_2', 258, 88],  # two
    ['4_3', 259, 89],  # three
    ['mod_left', 256, 90],  # zero
    ['mod_center', 266, 91],  # dot
    ['mod_right', 271, 104]]  # enter

# Generate lookup table for later.
KEYS_BY_ID = {x[1]: x for x in MACALLY_RFNUMKEY_KEY_LIST}


def mqtt_publish_event(mqtt_client, event, pressed_key_ids):
    valid_pressed_key_ids = filter(
        lambda i: i in KEYS_BY_ID.keys(), pressed_key_ids)
    if event.key in KEYS_BY_ID.keys():
        mqtt_payload = {
            'event_name': {pygame.KEYDOWN: 'pressed', pygame.KEYUP: 'released'}[event.type],
            'key': KEYS_BY_ID[event.key][0],
            'pressed_keys': [KEYS_BY_ID[i][0] for i in valid_pressed_key_ids]
        }

        # Uncomment the line below to debug.
        print(mqtt_payload, file=sys.stderr)
        mqtt_client.publish(MQTT_TOPIC, json.dumps(mqtt_payload))
    else:
        print(f"Unknown key: {event.key}", event.key, file=sys.stderr)


def on_connect(client, userdata, flags, rc):
    print("Connected with result code {0}".format(str(rc)), file=sys.stderr)
    #client.subscribe(f"{MQTT_TOPIC_PREFIX}/#")

def on_message(client, userdata, msg):
    print(f"Message received: {msg}", file=sys.stderr)


if __name__ == "__main__":
    print("Foo")
    # Just restart if anything fails, and keep trying.
    while True:
        try:
            # Set up PyGame.
            pygame.init()
            display = pygame.display.set_mode((720, 480), pygame.FULLSCREEN)

            # Set up MQTT.
            print("Attempting to connect to MQTT server now...", file=sys.stderr)
            mqtt_client = paho.mqtt.client.Client(MQTT_CLIENT_NAME)
            mqtt_client.on_connect = on_connect
            mqtt_client.on_message = on_message
            mqtt_client.connect('127.0.0.1', 1883)
            print(os.environ, file=sys.stderr)
            mqtt_client.username_pw_set(os.environ["MQTT_USER"],
                                        os.environ["MQTT_PASSWORD"])
            mqtt_client.loop_start()
            print("Connected.", file=sys.stderr)

            #pygame.display.set_mode((300, 300))
            #pygame.event.set_grab(True)

            # Main event loop.
            while True:
                for event in pygame.event.get():
                    if event.type == pygame.KEYDOWN and event.key == 113:  # 'q'
                        sys.exit(1)
                    if event.type in [pygame.KEYDOWN, pygame.KEYUP]:
                        key_pressed_by_id = pygame.key.get_pressed()
                        pressed_key_ids = numpy.nonzero(
                            key_pressed_by_id)[0].tolist()
                        mqtt_publish_event(mqtt_client, event, pressed_key_ids)

        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            print("Retrying in 1 second.", file=sys.stderr)
            time.sleep(1)
