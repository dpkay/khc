#!/usr/bin/env python3
"""
common.py — shared helpers for KHC services (macOS)

- Secrets come only from macOS Keychain using `security` CLI.
- MQTT client factory uses Paho v2 and connects to host:1883.
- Holds global constants (like MQTT_TOPIC_PREFIX) so all services stay in sync.
"""

from __future__ import annotations

import json
import subprocess
from typing import Any, Dict, Tuple

import paho.mqtt.client as mqtt

# ---------- Shared config ----------
MQTT_TOPIC_PREFIX = "kha/bedroom/windows_pc"


# ---------- Keychain ----------
def get_secret(label: str) -> str:
    """
    Fetch a secret from macOS Keychain (service name = khc:<LABEL>).
    Raises RuntimeError if not found.
    """
    r = subprocess.run(
        ["security", "find-generic-password", "-s", f"khc:{label}", "-w"],
        capture_output=True, text=True
    )
    if r.returncode != 0:
        raise RuntimeError(
            f"Missing secret '{label}' in Keychain.\n"
            f"Add it with:\n"
            f"  security add-generic-password -a \"$USER\" -s khc:{label} -w 'value'"
        )
    return r.stdout.strip()


def load_mqtt_secrets() -> Tuple[str, str, str]:
    """Convenience loader for MQTT creds: (host, username, password)."""
    host = get_secret("MQTT_HOST")
    user = get_secret("MQTT_USER")
    pwd  = get_secret("MQTT_PASSWORD")
    return host, user, pwd


# ---------- MQTT ----------
def create_and_connect_mqtt_client(client_id: str, keepalive: int = 30) -> mqtt.Client:
    """
    Create a Paho v2 client, set credentials from Keychain, and connect.
    NOTE: You still need to assign callbacks and (optionally) user_data.
    """
    host, user, pwd = load_mqtt_secrets()

    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id=client_id,
    )
    client.username_pw_set(user, pwd)
    client.connect(host, 1883, keepalive=keepalive)
    return client


# ---------- JSON ----------
def to_json(d: Dict[str, Any]) -> str:
    """Stable, compact JSON (no trailing spaces/newlines)."""
    return json.dumps(d, separators=(",", ":"))
