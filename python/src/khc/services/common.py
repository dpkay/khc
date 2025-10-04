#!/usr/bin/env python3
"""
common.py — shared helpers for KHC services (strict env-file mode)

Reads all secrets from ~/khc-private/.env.
If the file or any required key is missing, aborts immediately.

Example ~/.env:
    MQTT_HOST=192.168.1.11
    MQTT_PORT=1883
    MQTT_USER=kaeserchen
    MQTT_PASSWORD=supersecret
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, Tuple

import paho.mqtt.client as mqtt

# ---------- Shared config ----------
MQTT_TOPIC_PREFIX = "kha/bedroom/windows_pc"

# ---------- Secrets ----------
ENV_FILE = Path.home() / "khc-private" / ".env"


def _parse_env_file(path: Path) -> Dict[str, str]:
    if not path.is_file():
        sys.stderr.write(f"[fatal] Missing secrets file: {path}\n")
        sys.stderr.write("Create it with the required keys (MQTT_HOST, MQTT_PORT, MQTT_USER, MQTT_PASSWORD)\n")
        sys.exit(1)

    secrets: Dict[str, str] = {}
    for line in path.read_text().splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if "=" not in s:
            continue
        k, v = s.split("=", 1)
        secrets[k.strip()] = v.strip().strip('"').strip("'")

    for key in ("MQTT_HOST", "MQTT_USER", "MQTT_PASSWORD"):
        if key not in secrets:
            sys.stderr.write(f"[fatal] Missing {key} in {path}\n")
            sys.exit(1)

    return secrets


def load_mqtt_secrets() -> Tuple[str, str, str, int]:
    """Return (host, user, password, port)."""
    secrets = _parse_env_file(ENV_FILE)
    host = secrets["MQTT_HOST"]
    user = secrets["MQTT_USER"]
    pwd = secrets["MQTT_PASSWORD"]
    port = int(secrets.get("MQTT_PORT", "1883"))
    return host, user, pwd, port


# ---------- MQTT ----------
def create_and_connect_mqtt_client(client_id: str, keepalive: int = 30) -> mqtt.Client:
    host, user, pwd, port = load_mqtt_secrets()
    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id=client_id,
    )
    client.username_pw_set(user, pwd)
    client.connect(host, port, keepalive=keepalive)
    return client


# ---------- JSON ----------
def to_json(d: Dict[str, Any]) -> str:
    """Stable, compact JSON (no trailing spaces/newlines)."""
    return json.dumps(d, separators=(",", ":"))
