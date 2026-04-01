#!/usr/bin/python3
"""
Numpad -> MQTT bridge using evdev (no X11/pygame required).

Reads key events from the Macally RF numpad via /dev/input and publishes
JSON messages to MQTT. Supports modifier keys (hold mod_left/mod_center/
mod_right while pressing action keys).

Must run as root (or user with read access to /dev/input).
"""

import json
import sys
import time

import evdev

from khc.services.common import create_and_connect_mqtt_client

# --------------- Config ---------------
MQTT_CLIENT_NAME = "numpad_to_mqtt"
MQTT_TOPIC = "khc/livingroom/numpad"
DEVICE_PATH = "/dev/input/by-id/usb-Telink_Macally_RFKeyboard-if01-event-kbd"

# Map evdev keycodes to our logical key names.
# evdev KEY_* constants: https://python-evdev.readthedocs.io/en/latest/apidoc.html
KEYCODE_TO_NAME = {
    evdev.ecodes.KEY_BACKSPACE: '1_1',
    evdev.ecodes.KEY_EQUAL:    '1_2',   # Macally sends KEY_EQUAL, not KEY_KPEQUAL
    evdev.ecodes.KEY_KPSLASH:  '1_3',
    evdev.ecodes.KEY_KPASTERISK: '1_4',
    evdev.ecodes.KEY_KP7:      '2_1',
    evdev.ecodes.KEY_KP8:      '2_2',
    evdev.ecodes.KEY_KP9:      '2_3',
    evdev.ecodes.KEY_KPMINUS:  '2_4',
    evdev.ecodes.KEY_KP4:      '3_1',
    evdev.ecodes.KEY_KP5:      '3_2',
    evdev.ecodes.KEY_KP6:      '3_3',
    evdev.ecodes.KEY_KPPLUS:   '3_4',
    evdev.ecodes.KEY_KP1:      '4_1',
    evdev.ecodes.KEY_KP2:      '4_2',
    evdev.ecodes.KEY_KP3:      '4_3',
    evdev.ecodes.KEY_KP0:      'mod_left',
    evdev.ecodes.KEY_KPDOT:    'mod_center',
    evdev.ecodes.KEY_KPENTER:  'mod_right',
}


def find_device() -> evdev.InputDevice:
    """Open the numpad input device, retrying until found."""
    while True:
        try:
            dev = evdev.InputDevice(DEVICE_PATH)
            dev.grab()  # Exclusive access so keypresses don't leak to console
            print(f"Opened and grabbed: {dev.name} ({DEVICE_PATH})", file=sys.stderr)
            return dev
        except (FileNotFoundError, PermissionError, OSError) as e:
            print(f"Cannot open device ({e}), retrying in 2s...", file=sys.stderr)
            try:
                dev.close()
            except Exception:
                pass
            time.sleep(2)


def run(client):
    dev = find_device()
    pressed_keys: set[str] = set()

    print("Listening for numpad events...", file=sys.stderr)

    try:
        for event in dev.read_loop():
            if event.type != evdev.ecodes.EV_KEY:
                continue

            key_event = evdev.categorize(event)
            keycode = event.code
            name = KEYCODE_TO_NAME.get(keycode)

            if name is None:
                continue

            if key_event.keystate == evdev.KeyEvent.key_down:
                pressed_keys.add(name)
                payload = {
                    'event_name': 'pressed',
                    'key': name,
                    'pressed_keys': sorted(pressed_keys),
                }
                print(payload, file=sys.stderr)
                client.publish(MQTT_TOPIC, json.dumps(payload))

            elif key_event.keystate == evdev.KeyEvent.key_up:
                payload = {
                    'event_name': 'released',
                    'key': name,
                    'pressed_keys': sorted(pressed_keys),
                }
                client.publish(MQTT_TOPIC, json.dumps(payload))
                pressed_keys.discard(name)

    except OSError:
        print("Device disconnected", file=sys.stderr)
    finally:
        try:
            dev.ungrab()
        except Exception:
            pass


def main():
    while True:
        try:
            client = create_and_connect_mqtt_client(MQTT_CLIENT_NAME)
            client.loop_start()
            run(client)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
        print("Restarting in 2 seconds...", file=sys.stderr)
        time.sleep(2)


if __name__ == "__main__":
    main()
