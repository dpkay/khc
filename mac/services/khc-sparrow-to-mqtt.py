#!/usr/bin/env python3
"""
MIDI → MQTT bridge (batched)

Listens to MIDI CCs from 'Sparrow 5x5' and publishes
coalesced JSON updates to MQTT every ~20 ms.

Deps:
  pip install mido paho-mqtt
"""

from __future__ import annotations

import sys
import time
from typing import Dict

import mido
import paho.mqtt.client as mqtt

from common import MQTT_TOPIC_PREFIX, create_and_connect_mqtt_client, to_json

# --------------------------------------------------------------------
# Config
# --------------------------------------------------------------------
MQTT_CLIENT_NAME = "midi_to_mqtt"

MIDI_DEVICE_NAME = "Sparrow 5x5"
BATCH_INTERVAL   = 0.02  # seconds (~20 ms)

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
    """Create and connect an MQTT client; run network loop in a background thread."""
    client = create_and_connect_mqtt_client(MQTT_CLIENT_NAME)
    client.loop_start()
    return client

def publish_controls(client: mqtt.Client, pending: Dict[str, float]) -> None:
    """Publish all changed control values as one compact JSON payload."""
    if not pending:
        return
    topic = f"{MQTT_TOPIC_PREFIX}/controls"
    client.publish(topic, to_json(pending), qos=0, retain=False)

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

    pending: Dict[str, float] = {}
    last_flush = time.monotonic()

    print(f"[midi] Listening on '{MIDI_DEVICE_NAME}'")
    print("Press Ctrl+C to stop.\n")

    with port:
        for msg in port:
            if msg.type != "control_change" or not (0 <= msg.control <= 9):
                continue
            control_id = khc_control_id_from_cc(msg.control)
            pending[control_id] = normalize(msg.value)

            now = time.monotonic()
            if now - last_flush >= BATCH_INTERVAL:
                publish_controls(client, pending)
                pending.clear()
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
