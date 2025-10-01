#!/usr/bin/env python3
"""
MIDI → MQTT bridge (batched)

Listens to MIDI CCs from 'Sparrow 5x5' and publishes
coalesced JSON updates to MQTT every ~20 ms.

Data flow
---------
- MIDI CC messages 0–9 are mapped to logical control IDs:
    dial_1..5 and fader_1..5
- Values are normalized to floats in [0.0, 1.0]
- Rapid bursts are batched: every 20 ms, all changed values
  are published as one JSON dict to MQTT.

Example payload:
    {"fader_2": 0.543, "dial_1": 0.118}
"""

import json
import os
import sys
import time
from typing import Dict

import mido
import paho.mqtt.client as mqtt

# --------------------------------------------------------------------
# Config
# --------------------------------------------------------------------
MQTT_CLIENT_NAME = "midi_to_mqtt"
MQTT_TOPIC_PREFIX = "kha/bedroom/windows_pc"

MQTT_HOST = os.environ["MQTT_HOST"]
MQTT_USER = os.environ["MQTT_USER"]
MQTT_PASSWORD = os.environ["MQTT_PASSWORD"]

MIDI_DEVICE_NAME = "Sparrow 5x5"
BATCH_INTERVAL = 0.02  # seconds (~20 ms)

# --------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------
def khc_control_id_from_cc(cc: int) -> str:
    """Map MIDI CC 0–9 to logical control IDs (dial_1..5, fader_1..5)."""
    return f"dial_{cc + 1}" if cc < 5 else f"fader_{cc - 4}"

def normalize(value: int) -> float:
    """Convert MIDI 0–127 integer into normalized float 0.0–1.0."""
    return value / 127.0

# --------------------------------------------------------------------
# MQTT setup & publishing
# --------------------------------------------------------------------
def create_mqtt_client() -> mqtt.Client:
    """Create and connect an MQTT client with background network loop."""
    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id=MQTT_CLIENT_NAME,
    )
    client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    client.connect(MQTT_HOST, 1883, keepalive=30)
    client.loop_start()
    return client

def publish_controls(client: mqtt.Client, pending_khc_control_value_by_id: Dict[str, float]) -> None:
    """
    Publish all changed control values as one JSON payload.

    Payload example:
        {"fader_2": 0.543, "dial_1": 0.118}
    """
    if not pending_khc_control_value_by_id:
        return
    topic = f"{MQTT_TOPIC_PREFIX}/controls"
    payload = json.dumps(pending_khc_control_value_by_id)
    client.publish(topic, payload, qos=0, retain=False)
    # print(f"[midi→mqtt] {topic} {payload}")

# --------------------------------------------------------------------
# MIDI processing
# --------------------------------------------------------------------
def run_midi_loop(client: mqtt.Client) -> None:
    """Listen for MIDI CC messages and flush them to MQTT in batches."""
    try:
        port = mido.open_input(MIDI_DEVICE_NAME)
    except IOError:
        print(f"[error] MIDI device '{MIDI_DEVICE_NAME}' not found.", file=sys.stderr)
        sys.exit(1)

    pending_khc_control_value_by_id: Dict[str, float] = {}
    last_flush = time.monotonic()

    print(f"[midi] Listening on '{MIDI_DEVICE_NAME}'")
    print("Press Ctrl+C to stop.\n")

    with port:
        for msg in port:
            if msg.type != "control_change" or not (0 <= msg.control <= 9):
                continue

            control_id = khc_control_id_from_cc(msg.control)
            value = normalize(msg.value)

            # Mark this control as changed since last flush
            pending_khc_control_value_by_id[control_id] = value

            # Flush batch every BATCH_INTERVAL
            now = time.monotonic()
            if now - last_flush >= BATCH_INTERVAL:
                publish_controls(client, pending_khc_control_value_by_id)
                pending_khc_control_value_by_id.clear()
                last_flush = now

# --------------------------------------------------------------------
# Main
# --------------------------------------------------------------------
def main() -> int:
    """Entry point: setup MQTT and run the MIDI loop until Ctrl+C."""
    client = create_mqtt_client()
    try:
        run_midi_loop(client)
    except KeyboardInterrupt:
        print("\n[loop] Stopping cleanly…")
    finally:
        client.loop_stop()
        client.disconnect()
    return 0

if __name__ == "__main__":
    sys.exit(main())
