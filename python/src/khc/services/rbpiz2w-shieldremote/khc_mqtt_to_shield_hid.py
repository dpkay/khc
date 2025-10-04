#!/usr/bin/env python3
"""
khc.services.mqtt_to_shield_hid

MQTT → USB HID bridge for NVIDIA Shield

- Subscribes to MQTT and writes HID reports to:
    /dev/hidg0  (Boot Keyboard: arrows, Enter, Esc)
    /dev/hidg1  (Consumer Control: play/pause, next/prev, vol±)

Environment variables (systemd EnvironmentFile):
  MQTT_HOST      (e.g. 192.168.1.11)
  MQTT_PORT      (default 1883)
  MQTT_USER      (optional)
  MQTT_PASSWORD  (optional)
  MQTT_TOPIC     (e.g. kha/livingroom/shield/press_key)
  MQTT_DEBUG     (optional: "1" enables DEBUG logs)

Run your systemd unit with python -u so logs are unbuffered:
  ExecStart=/home/dpkay/khc/.venv/bin/python -u -m khc.services.mqtt_to_shield_hid
"""

import os
import json
import logging
import signal
from typing import Callable, Dict

import paho.mqtt.client as mqtt


# ────────────────────────── Env / Config ──────────────────────────

MQTT_HOST = os.environ.get("MQTT_HOST", "127.0.0.1")
MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))
MQTT_USER = os.environ.get("MQTT_USER", "")
MQTT_PASS = os.environ.get("MQTT_PASSWORD", "")
TOPIC     = os.environ.get("MQTT_TOPIC", "kha/livingroom/shield/press_key")
DEBUG_ON  = os.environ.get("MQTT_DEBUG", "") == "1"

KEYBOARD_DEV = "/dev/hidg0"
CONSUMER_DEV = "/dev/hidg1"


# ───────────────────────────── Logging ─────────────────────────────

logging.basicConfig(
    level=logging.DEBUG if DEBUG_ON else logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger("mqtt_to_shield_hid")


# ───────────────────────────── HID I/O ─────────────────────────────
# Keyboard scancodes (HID Usage Page 0x07)
KEY_ENTER = 0x28
KEY_ESC   = 0x29
KEY_LEFT  = 0x50
KEY_DOWN  = 0x51
KEY_UP    = 0x52
KEY_RIGHT = 0x4F

def _kb_report(keycode: int, modifiers: int = 0) -> bytes:
    """8-byte Boot Keyboard report: [mods, reserved, k1..k6]."""
    return bytes([modifiers, 0, keycode, 0, 0, 0, 0, 0])

def _kb_tap(keycode: int, modifiers: int = 0) -> None:
    """Send press+release for a keyboard key."""
    try:
        with open(KEYBOARD_DEV, "wb", buffering=0) as f:
            f.write(_kb_report(keycode, modifiers))  # press
            f.write(b"\x00" * 8)                     # release
    except Exception as e:
        log.error("Keyboard HID write failed: %s", e)

# Consumer Control bits (HID Usage Page 0x0C) — order must match your descriptor
CC_PLAY_PAUSE = 0
CC_NEXT       = 1
CC_PREV       = 2
CC_VOL_UP     = 3
CC_VOL_DOWN   = 4

def _cc_report(*bit_positions: int) -> bytes:
    """2-byte Consumer Control report; we only use the first byte."""
    b0 = 0
    for b in bit_positions:
        b0 |= (1 << b)
    return bytes([b0, 0x00])

def _cc_tap(*bit_positions: int) -> None:
    """Send press+release for consumer control bits."""
    try:
        with open(CONSUMER_DEV, "wb", buffering=0) as f:
            f.write(_cc_report(*bit_positions))  # press
            f.write(b"\x00\x00")                 # release
    except Exception as e:
        log.error("Consumer HID write failed: %s", e)


# Map incoming payload "name" → action
NAME_TO_ACTION: Dict[str, Callable[[], None]] = {
    "up":         lambda: _kb_tap(KEY_UP),
    "down":       lambda: _kb_tap(KEY_DOWN),
    "left":       lambda: _kb_tap(KEY_LEFT),
    "right":      lambda: _kb_tap(KEY_RIGHT),
    "center":     lambda: _kb_tap(KEY_ENTER),   # DPAD_CENTER
    "back":       lambda: _kb_tap(KEY_ESC),
    "play_pause": lambda: _cc_tap(CC_PLAY_PAUSE),
    "next":       lambda: _cc_tap(CC_NEXT),
    "prev":       lambda: _cc_tap(CC_PREV),
    "vol_up":     lambda: _cc_tap(CC_VOL_UP),
    "vol_down":   lambda: _cc_tap(CC_VOL_DOWN),
}


# ─────────────────────────── MQTT Callbacks ───────────────────────────

def _on_connect(client: mqtt.Client, userdata, flags, reason_code, properties=None):
    """paho-mqtt v2 on_connect signature."""
    log.info("MQTT connected: reason_code=%s", reason_code)
    if reason_code == mqtt.MQTT_ERR_SUCCESS or reason_code == 0:
        # Subscribe to exact topic from env (no wildcard by default)
        res = client.subscribe(TOPIC)
        log.info("Subscribed to %r: %s", TOPIC, res)
    else:
        log.error("MQTT connect failed with reason_code=%s", reason_code)

def _on_subscribe(client, userdata, mid, granted_qos):
    log.info("SUBACK mid=%s qos=%s", mid, granted_qos)

def _on_message(client: mqtt.Client, userdata, msg: mqtt.MQTTMessage):
    try:
        payload = json.loads(msg.payload.decode("utf-8", "ignore"))
        name = payload.get("name")
        log.info("MQTT msg on %r: %s", msg.topic, payload)
        fn = NAME_TO_ACTION.get(name)
        if fn:
            fn()
            log.info("Sent: %s", name)
        else:
            log.warning("Unknown key name: %r", name)
    except Exception as e:
        log.exception("Error handling MQTT message: %s", e)

def _on_log(client, userdata, level, buf):
    # Very verbose; only shows when DEBUG_ON=1
    log.debug("PAHO: %s", buf)


# ─────────────────────────── Main / Loop ───────────────────────────

_running = True
def _handle_sigterm(signum, frame):
    global _running
    _running = False
    log.info("SIGTERM received, shutting down...")

signal.signal(signal.SIGTERM, _handle_sigterm)
signal.signal(signal.SIGINT, _handle_sigterm)


def main():
    # Early visibility on startup & config
    log.info("Starting MQTT→HID | host=%s:%s topic=%r", MQTT_HOST, MQTT_PORT, TOPIC)

    # Warn early if gadget nodes aren’t present (they may appear shortly after boot)
    for path in (KEYBOARD_DEV, CONSUMER_DEV):
        if not os.path.exists(path):
            log.warning("HID device not found yet: %s (hidg.service still starting?)", path)

    c = mqtt.Client(client_id="khc-mqtt-to-shield-hid", protocol=mqtt.MQTTv311)
    c.enable_logger(log)  # route paho logs through our logger
    if MQTT_USER or MQTT_PASS:
        c.username_pw_set(MQTT_USER, MQTT_PASS)

    # Be gentle on reconnect storms
    c.reconnect_delay_set(min_delay=1, max_delay=30)

    # Wire callbacks
    c.on_connect = _on_connect
    c.on_subscribe = _on_subscribe
    c.on_message = _on_message
    c.on_log = _on_log if DEBUG_ON else None

    # Connect and loop forever (retry_first_connection ensures reconnect attempts)
    c.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
    try:
        while _running:
            c.loop(timeout=1.0)
    finally:
        try:
            c.disconnect()
        except Exception:
            pass
        log.info("Stopped.")
        
if __name__ == "__main__":
    main()
