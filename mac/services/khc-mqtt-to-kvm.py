#!/usr/bin/env python3
"""
Level1Techs KVM controller: MQTT → USB serial (macOS)

Listens on MQTT for a JSON payload like:
  topic:  {MQTT_TOPIC_PREFIX}/kvm/set_source
  body:   {"source_name": "corp_mac"}

and sends the corresponding ASCII command to the KVM via its USB serial port.

Deps:
  pip install paho-mqtt pyserial
"""

from __future__ import annotations

import json
import sys
from typing import Dict, Optional

import paho.mqtt.client as mqtt
import serial as pyserial

from common import MQTT_TOPIC_PREFIX, create_and_connect_mqtt_client

# --------------------------------------------------------------------
# Config (adjust SERIAL_PORT to match your Mac's device path)
# --------------------------------------------------------------------
MQTT_CLIENT_NAME  = "mqtt_from_and_to_kvm"

# Example from your system_profiler results; change as needed:
SERIAL_PORT        = "/dev/tty.usbmodemB7CD849C82261"
SERIAL_BAUD        = 9600
SERIAL_TIMEOUT_SEC = 1

# Map human-friendly source names → KVM ASCII commands (bytes)
# (The Level1 KVM expects CRLF line endings.)
SOURCE_TO_CMD: Dict[str, bytes] = {
    "personal_windows": b"9:V=1\r\n",
    "corp_mac":         b"9:V=3\r\n",
    "corp_windows":     b"9:V=4\r\n",
}

# --------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------
def write_kvm_command(ser: pyserial.Serial, cmd: bytes) -> None:
    """Send a single command to the KVM over serial."""
    ser.write(cmd)
    ser.flush()

# --------------------------------------------------------------------
# MQTT callbacks (v2 API signatures)
# --------------------------------------------------------------------
def on_mqtt_connected(
    client: mqtt.Client,
    userdata_serial: pyserial.Serial,
    connect_flags: mqtt.ConnectFlags,
    reason_code: mqtt.ReasonCode,
    properties: Optional[mqtt.Properties],
):
    print(f"[mqtt] Connected: reason={reason_code}")
    client.subscribe(f"{MQTT_TOPIC_PREFIX}/kvm/#")

def on_mqtt_message_received(
    client: mqtt.Client,
    userdata_serial: pyserial.Serial,
    msg: mqtt.MQTTMessage,
):
    """Handle incoming MQTT messages and route to the KVM."""
    if msg.topic != f"{MQTT_TOPIC_PREFIX}/kvm/set_source":
        return

    payload = msg.payload.decode("utf-8", "ignore")
    try:
        data = json.loads(payload)
    except Exception as e:
        print(f"[mqtt] bad JSON: {payload!r} ({e})")
        return

    source_name = data.get("source_name")
    if not isinstance(source_name, str):
        print(f"[bridge] missing/invalid 'source_name' in payload: {data!r}")
        return

    cmd = SOURCE_TO_CMD.get(source_name)
    if not cmd:
        print(f"[bridge] unknown source: {source_name!r}")
        return

    try:
        print(f"[kvm] switching to {source_name}")
        write_kvm_command(userdata_serial, cmd)
    except Exception as e:
        print(f"[kvm] serial write failed: {e}")

# --------------------------------------------------------------------
# Main
# --------------------------------------------------------------------
def main() -> int:
    # Open serial once and pass it to MQTT callbacks via user_data
    print(f"[serial] Opening {SERIAL_PORT} @ {SERIAL_BAUD}…")
    ser = pyserial.Serial(SERIAL_PORT, baudrate=SERIAL_BAUD, timeout=SERIAL_TIMEOUT_SEC)

    print(f"[mqtt] Connecting as {MQTT_CLIENT_NAME}")
    client = create_and_connect_mqtt_client(MQTT_CLIENT_NAME)
    client.on_connect = on_mqtt_connected
    client.on_message = on_mqtt_message_received
    client.user_data_set(ser)

    try:
        client.loop_forever()  # blocks
    except KeyboardInterrupt:
        print("\n[loop] Stopping…")
    finally:
        try: ser.close()
        except Exception: pass
        try: client.disconnect()
        except Exception: pass
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"[fatal] {e.__class__.__name__}: {e}")
        sys.exit(1)
