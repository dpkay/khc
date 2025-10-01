#!/usr/bin/env python3
"""
MQTT → REAPER (OSC) bridge

Listens for MQTT JSON payloads and forwards mapped parameters
to REAPER via OSC.

Dependencies:
  pip install paho-mqtt python-osc
"""

import json
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

import paho.mqtt.client as mqtt
from pythonosc.udp_client import SimpleUDPClient

# --------------------------------------------------------------------
# Hardcoded configuration
# --------------------------------------------------------------------
MQTT_CLIENT_NAME = "mqtt_to_reaper_osc"
MQTT_TOPIC_PREFIX = "kha/bedroom/windows_pc"

REAPER_HOST = "127.0.0.1"
REAPER_OSC_PORT = 1234

# These still come from env, since they’re secrets
MQTT_HOST = os.environ["MQTT_HOST"]
MQTT_USER = os.environ["MQTT_USER"]
MQTT_PASSWORD = os.environ["MQTT_PASSWORD"]

# Map from MQTT parameter keys → REAPER OSC addresses
PARAM_TO_OSC: Dict[str, str] = {
    "input_volume__windows_laptop": "/track/2/volume",
    "input_volume__external_laptop": "/track/3/volume",
    "output_volume__speakers": "/track/1/send/1/volume",
    "output_volume__regular_headphones": "/track/1/send/2/volume",
}

# --------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------
def build_osc_messages(mqtt_params: Dict[str, Any]) -> List[Tuple[str, float]]:
    """Turn a dict of MQTT params into (osc_address, float_value) tuples."""
    msgs: List[Tuple[str, float]] = []
    for key, addr in PARAM_TO_OSC.items():
        if key in mqtt_params:
            try:
                msgs.append((addr, float(mqtt_params[key])))
            except (TypeError, ValueError):
                print(f"[warn] Ignoring non-float value for {key}: {mqtt_params[key]!r}")
    return msgs

def send_osc_messages(osc_messages: List[Tuple[str, float]], osc_client: SimpleUDPClient) -> None:
    """Send OSC messages to REAPER."""
    for address, value in osc_messages:
        osc_client.send_message(address, value)

# --------------------------------------------------------------------
# MQTT Callbacks (v2 API signatures)
# --------------------------------------------------------------------
def on_mqtt_connected(
    client: mqtt.Client,
    userdata,
    connect_flags: mqtt.ConnectFlags,
    reason_code: mqtt.ReasonCode,
    properties: Optional[mqtt.Properties],
):
    print(f"[mqtt] Connected: reason={reason_code}")
    client.subscribe(f"{MQTT_TOPIC_PREFIX}/daw/#")

def on_mqtt_message_received(client: mqtt.Client, userdata_osc_client: SimpleUDPClient, msg: mqtt.MQTTMessage):
    """Decode incoming MQTT message and forward as OSC if it matches our topic."""
    payload_decoded = msg.payload.decode("utf-8", "ignore")
    try:
        payload_json = json.loads(payload_decoded)
    except Exception as e:
        print(f"[mqtt] Bad JSON: {payload_decoded!r} ({e})")
        return

    if msg.topic == f"{MQTT_TOPIC_PREFIX}/daw/set_params":
        osc_messages = build_osc_messages(payload_json)
        if osc_messages:
            print(f"[bridge] Forwarding {len(osc_messages)} params to REAPER")
            send_osc_messages(osc_messages, userdata_osc_client)

# --------------------------------------------------------------------
# Main
# --------------------------------------------------------------------
def main() -> int:
    # Create OSC client
    print(f"[osc] Connecting to REAPER at {REAPER_HOST}:{REAPER_OSC_PORT}")
    osc_client = SimpleUDPClient(REAPER_HOST, REAPER_OSC_PORT)

    # Create MQTT client (v2 API)
    print(f"[mqtt] Connecting to broker {MQTT_HOST} as {MQTT_CLIENT_NAME}")
    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
                         client_id=MQTT_CLIENT_NAME)
    client.on_connect = on_mqtt_connected
    client.on_message = on_mqtt_message_received
    client.user_data_set(osc_client)
    client.username_pw_set(MQTT_USER, MQTT_PASSWORD)

    client.connect(MQTT_HOST, 1883, keepalive=30)

    # Simplest event loop: block until Ctrl-C
    client.loop_forever()

    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n[loop] Stopping cleanly…")
