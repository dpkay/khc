#!/usr/bin/env python3
"""
MIDI → MQTT bridge (batched, verbose)

Listens to MIDI CCs from a controller and publishes
coalesced JSON updates to MQTT every ~20 ms.

Deps:
  pip install mido paho-mqtt
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from typing import Dict, List, Optional

import mido
import paho.mqtt.client as mqtt

from khc.services.common import MQTT_TOPIC_PREFIX, create_and_connect_mqtt_client, to_json

# --------------------------------------------------------------------
# Config (can be overridden via --device/--debug)
# --------------------------------------------------------------------
MQTT_CLIENT_NAME = "midi_to_mqtt"
MIDI_DEVICE_NAME = "Sparrow 5x5"
BATCH_INTERVAL   = 0.02  # seconds (~20 ms)

# --------------------------------------------------------------------
# Logging
# --------------------------------------------------------------------
LOG = logging.getLogger("midi_to_mqtt")


def setup_logging(debug: bool) -> None:
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s.%(msecs)03d %(levelname)-7s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    # Make mido a bit quieter unless we’re debugging
    logging.getLogger("mido").setLevel(logging.WARNING if not debug else logging.DEBUG)


# --------------------------------------------------------------------
# MIDI helpers
# --------------------------------------------------------------------
def list_midi_inputs() -> List[str]:
    names = mido.get_input_names()
    LOG.info("Available MIDI input devices (%d):", len(names))
    for i, n in enumerate(names):
        LOG.info("  [%d] %s", i, n)
    return names


def resolve_device_name(requested: str) -> Optional[str]:
    """Try exact match, then case-insensitive 'contains' match."""
    names = list_midi_inputs()
    if not names:
        return None

    # Exact match first
    if requested in names:
        LOG.info("Using exact match for MIDI device: %s", requested)
        return requested

    # Case-insensitive partial match
    lowered = requested.lower()
    matches = [n for n in names if lowered in n.lower()]
    if len(matches) == 1:
        LOG.info("Using partial match for MIDI device: %s (matched '%s')", requested, matches[0])
        return matches[0]
    elif len(matches) > 1:
        LOG.warning("Multiple partial matches for '%s': %s", requested, matches)
        LOG.warning("Please choose one with --device.")
        return None

    LOG.error("No MIDI device matched '%s'.", requested)
    return None


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
    LOG.info("Connecting to MQTT as client '%s'…", MQTT_CLIENT_NAME)
    client = create_and_connect_mqtt_client(MQTT_CLIENT_NAME)
    client.loop_start()
    LOG.info("MQTT loop started.")
    return client


def publish_controls(client: mqtt.Client, pending: Dict[str, float]) -> None:
    """Publish all changed control values as one compact JSON payload."""
    if not pending:
        return
    topic = f"{MQTT_TOPIC_PREFIX}/controls"
    payload = to_json(pending)
    LOG.debug("Publishing %d control(s) → %s", len(pending), topic)
    # Show a single-line preview to help debug downstream subscribers:
    # LOG.info("→ MQTT %s %s", topic, payload)

    result = client.publish(topic, payload, qos=0, retain=False)
    # Some clients return a tuple (rc, mid); paho 2.x returns MQTTMessageInfo
    try:
        result.wait_for_publish(timeout=1.0)
    except Exception:  # noqa: BLE001
        pass


# --------------------------------------------------------------------
# MIDI processing
# --------------------------------------------------------------------
def run_midi_loop(client: mqtt.Client, device_name: str) -> None:
    """Listen for MIDI CC messages and flush them to MQTT in batches."""
    resolved = resolve_device_name(device_name)
    if not resolved:
        LOG.error("MIDI device '%s' not found. Exiting.", device_name)
        sys.exit(1)

    try:
        port = mido.open_input(resolved)
    except IOError as e:
        LOG.error("Failed to open MIDI input '%s': %s", resolved, e)
        sys.exit(1)


    pending: Dict[str, float] = {}
    last_published: Dict[str, float] = {}
    last_flush = time.monotonic()
    last_msg_time = time.monotonic()
    DEADBAND = 2.0 / 127.0  # ignore changes smaller than ~2 MIDI steps

    LOG.info("Listening on MIDI input: '%s'", resolved)
    LOG.info("Batch interval: %.0f ms", BATCH_INTERVAL * 1000.0)
    LOG.info("Press Ctrl+C to stop.\n")

    with port:
        for msg in port:
            LOG.debug("MIDI raw: %s", msg)

            if msg.type != "control_change":
                LOG.debug("Ignoring non-CC message: %s", msg.type)
                continue
            if not (0 <= msg.control <= 9):
                LOG.debug("Ignoring CC outside 0–9: CC%d val=%s", msg.control, getattr(msg, "value", None))
                continue

            control_id = khc_control_id_from_cc(msg.control)
            value_norm = normalize(msg.value)
            prev = last_published.get(control_id)
            if prev is not None and abs(value_norm - prev) < DEADBAND:
                continue
            pending[control_id] = value_norm
            LOG.debug("Staged %s = %.3f (CC%d %d)", control_id, value_norm, msg.control, msg.value)
            last_msg_time = time.monotonic()

            now = time.monotonic()
            if now - last_flush >= BATCH_INTERVAL:
                publish_controls(client, pending)
                last_published.update(pending)
                pending.clear()
                last_flush = now

            # Lightweight heartbeat if nothing arrived for a while
            if now - last_msg_time > 5.0:
                # LOG.info("No MIDI activity in the last %.1fs. Still listening…", now - last_msg_time)
                last_msg_time = now  # avoid spamming


# --------------------------------------------------------------------
# Main / CLI
# --------------------------------------------------------------------
def parse_args(argv: List[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="MIDI → MQTT bridge (batched)")
    p.add_argument("--device", "-d", default=MIDI_DEVICE_NAME,
                   help="MIDI input device name (exact or partial match). Default: %(default)s")
    p.add_argument("--list", action="store_true",
                   help="List available MIDI input devices and exit.")
    p.add_argument("--debug", action="store_true",
                   help="Enable verbose debug logging.")
    return p.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    setup_logging(args.debug)

    if args.list:
        names = list_midi_inputs()
        if not names:
            LOG.error("No MIDI input devices found.")
            return 1
        return 0

    client = create_mqtt_client()
    try:
        run_midi_loop(client, args.device)
    except KeyboardInterrupt:
        LOG.info("Stopping cleanly (Ctrl+C)…")
    finally:
        LOG.info("Stopping MQTT loop and disconnecting…")
        client.loop_stop()
        client.disconnect()
    return 0


if __name__ == "__main__":
    sys.exit(main())
