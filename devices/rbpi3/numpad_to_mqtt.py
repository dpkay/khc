#!/usr/bin/python3
"""
Numpad → MQTT bridge using evdev (no X11/pygame required).

Reads key events from the Macally RF numpad via /dev/input and publishes
JSON messages to MQTT. Supports modifier keys (hold mod_left/mod_center/
mod_right while pressing action keys).

Requires: python-evdev, paho-mqtt
Must run as root (or user with read access to /dev/input).
"""

import json
import os
import sys
import time
from pathlib import Path

import evdev
import paho.mqtt.client as mqtt

# --------------- Config ---------------
MQTT_TOPIC = "khc/livingroom/numpad"
DEVICE_PATH = "/dev/input/by-id/usb-Telink_Macally_RFKeyboard-if01-event-kbd"

# Map evdev keycodes to our logical key names.
# evdev KEY_* constants: https://python-evdev.readthedocs.io/en/latest/apidoc.html
KEYCODE_TO_NAME = {
    evdev.ecodes.KEY_BACKSPACE: '1_1',
    evdev.ecodes.KEY_KPEQUAL:  '1_2',   # numpad =
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


def load_env(path: str) -> dict:
    """Read KEY=VALUE pairs from a file."""
    env = {}
    p = Path(path).expanduser()
    if p.exists():
        for line in p.read_text().splitlines():
            line = line.strip()
            if line and '=' in line and not line.startswith('#'):
                k, v = line.split('=', 1)
                env[k.strip()] = v.strip()
    return env


def create_mqtt_client() -> mqtt.Client:
    # Try ~/khc-private/.env first, fall back to environment variables
    # Use SUDO_USER's home if running via sudo, otherwise current user's home
    home = Path.home()
    sudo_user = os.environ.get("SUDO_USER")
    if sudo_user:
        home = Path(f"/home/{sudo_user}")
    env = load_env(str(home / "khc-private" / ".env"))
    host = env.get("MQTT_HOST", os.environ.get("MQTT_HOST", "127.0.0.1"))
    port = int(env.get("MQTT_PORT", os.environ.get("MQTT_PORT", "1883")))
    user = env.get("MQTT_USER", os.environ.get("MQTT_USER", ""))
    password = env.get("MQTT_PASSWORD", os.environ.get("MQTT_PASSWORD", ""))

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="numpad_to_mqtt")
    if user:
        client.username_pw_set(user, password)
    client.on_connect = lambda *_: print(f"MQTT connected to {host}:{port}", file=sys.stderr)
    client.on_disconnect = lambda *_: print("MQTT disconnected", file=sys.stderr)
    client.connect(host, port, keepalive=30)
    client.loop_start()
    return client


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


def run(client: mqtt.Client):
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


if __name__ == "__main__":
    while True:
        try:
            client = create_mqtt_client()
            run(client)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
        print("Restarting in 2 seconds...", file=sys.stderr)
        time.sleep(2)
