#!/usr/bin/env python3
"""
MQTT → USB HID bridge for Shield

- /dev/hidg0 : Boot keyboard (arrows, Enter, Esc) — 8 bytes per report
- /dev/hidg1 : Consumer control (media keys)      — 3 bytes per report (Report ID = 0x01)

Env (provided by systemd EnvironmentFile):
  MQTT_HOST, MQTT_PORT, MQTT_USER, MQTT_PASSWORD, MQTT_TOPIC
"""

import os
import json
import logging
import paho.mqtt.client as mqtt

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

# ---------------- Env ----------------
MQTT_HOST = os.environ.get("MQTT_HOST", "127.0.0.1")
MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))
MQTT_USER = os.environ.get("MQTT_USER", "")
MQTT_PASS = os.environ.get("MQTT_PASSWORD", "")
TOPIC     = os.environ.get("MQTT_TOPIC", "kha/livingroom/shield/press_key")

KEYBOARD_DEV = "/dev/hidg0"
CONSUMER_DEV = "/dev/hidg1"

# ------------- Keyboard (8 bytes) -------------
# byte0 = modifiers, byte1 = reserved, byte2..7 = keycodes
KEY_ENTER = 0x28
KEY_ESC   = 0x29
KEY_LEFT  = 0x50
KEY_DOWN  = 0x51
KEY_UP    = 0x52
KEY_RIGHT = 0x4F

def _kb_report(keycode: int, modifiers: int = 0) -> bytes:
    return bytes([modifiers, 0, keycode, 0, 0, 0, 0, 0])

def _kb_tap(keycode: int, modifiers: int = 0) -> None:
    with open(KEYBOARD_DEV, "wb", buffering=0) as f:
        f.write(_kb_report(keycode, modifiers))    # press
        f.write(b"\x00" * 8)                       # release

# --------- Consumer Control (3 bytes) ----------
# We added Report ID = 0x01 in setup_hid.py, so the report is:
#   [0] = 0x01 (Report ID)
#   [1] = bitfield: bit0=Play/Pause, bit1=Next, bit2=Prev, bit3=Vol+, bit4=Vol-
#   [2] = 0x00 (padding)
CC_PLAY_PAUSE = 0
CC_NEXT       = 1
CC_PREV       = 2
CC_VOL_UP     = 3
CC_VOL_DOWN   = 4

def _cc_report(*bit_positions: int) -> bytes:
    b0 = 0
    for b in bit_positions:
        b0 |= (1 << b)
    return bytes([0x01, b0, 0x00])  # ReportID=1, bits, pad

def _cc_tap(*bit_positions: int) -> None:
    with open(CONSUMER_DEV, "wb", buffering=0) as f:
        f.write(_cc_report(*bit_positions))        # press
        f.write(bytes([0x01, 0x00, 0x00]))         # release

# ------------- Routing -------------
NAME_TO_ACTION = {
    "up":         lambda: _kb_tap(KEY_UP),
    "down":       lambda: _kb_tap(KEY_DOWN),
    "left":       lambda: _kb_tap(KEY_LEFT),
    "right":      lambda: _kb_tap(KEY_RIGHT),
    "center":     lambda: _kb_tap(KEY_ENTER),      # DPAD_CENTER
    "back":       lambda: _kb_tap(KEY_ESC),

    "play_pause": lambda: _cc_tap(CC_PLAY_PAUSE),
    "next":       lambda: _cc_tap(CC_NEXT),
    "prev":       lambda: _cc_tap(CC_PREV),
    "vol_up":     lambda: _cc_tap(CC_VOL_UP),
    "vol_down":   lambda: _cc_tap(CC_VOL_DOWN),
}

# ------------- MQTT callbacks -------------
def _on_connect(client, userdata, flags, reason_code, properties=None):
    logging.info("MQTT connected: reason_code=%s", reason_code)
    if reason_code == 0:
        rc = client.subscribe(TOPIC)
        logging.info("Subscribed to %s: %s", TOPIC, rc)
    else:
        logging.error("MQTT connect failed: %s", reason_code)

def _on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode("utf-8", "ignore"))
        name = payload.get("name")
        fn = NAME_TO_ACTION.get(name)
        logging.info("MQTT msg on %s: %s", msg.topic, payload)
        if fn:
            fn()
        else:
            logging.warning("Unknown key: %s", name)
    except Exception as e:
        logging.exception("Error handling message: %s", e)

def main():
    logging.info("Starting MQTT→HID | host=%s:%s topic=%s", MQTT_HOST, MQTT_PORT, TOPIC)
    c = mqtt.Client(client_id="khc-mqtt-to-shield-hid", protocol=mqtt.MQTTv311)
    if MQTT_USER or MQTT_PASS:
        c.username_pw_set(MQTT_USER, MQTT_PASS)
    c.on_connect = _on_connect
    c.on_message = _on_message
    c.connect(MQTT_HOST, MQTT_PORT, 60)
    c.loop_forever()

if __name__ == "__main__":
    main()
