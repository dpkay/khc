#!/bin/bash
set -e

# ------------------------------
# install.sh – setup script for rbpiz2w-shieldremote
#
# Purpose:
#   - Configure the Pi Zero 2W to impersonate a USB keyboard (HID gadget).
#   - Install systemd service units so the setup + MQTT bridge run automatically.
#
# After this, you just plug the Pi into the Shield over USB,
# publish MQTT messages, and the Shield thinks a remote is pressing keys.
# ------------------------------

USER_HOME="${HOME}"
DEVICE_DIR="${USER_HOME}/khc/devices/rbpiz2w-shieldremote"
PY_ROOT="${USER_HOME}/khc/python"
VENV="${USER_HOME}/khc/.venv"
ENV_FILE="${USER_HOME}/khc-private/.env"

# 0. Sanity check: required private env file
# ------------------------------
echo "Checking for ${ENV_FILE} ..."
if [[ ! -f "${ENV_FILE}" ]]; then
  echo "ERROR: Missing ${ENV_FILE}"
  echo "Create it with your MQTT settings, e.g.:"
  echo "  MQTT_HOST=192.168.1.11"
  echo "  MQTT_PORT=1883"
  echo "  MQTT_USER=kaeserchen"
  echo "  MQTT_PASSWORD=..."
  echo "  MQTT_TOPIC=kha/livingroom/shield/press_key"
  exit 1
fi

# 1. Enable HID gadget at boot
# ------------------------------
# dtoverlay=dwc2 tells the kernel to load the USB controller driver in "device" mode
# (so the Pi can pretend to *be* a USB gadget, not just host devices like mice).
#
# libcomposite is a kernel module that provides the "ConfigFS" framework for creating
# gadgets (HID keyboard, serial, Ethernet-over-USB, etc).
#
# Modern way to load modules: drop .conf files in /etc/modules-load.d/
echo "Ensuring USB gadget kernel modules load at boot..."
echo "dwc2" | sudo tee /etc/modules-load.d/dwc2.conf
echo "libcomposite" | sudo tee /etc/modules-load.d/libcomposite.conf

# Also make sure dtoverlay=dwc2 is in /boot/firmware/config.txt
if ! grep -q "dtoverlay=dwc2" /boot/firmware/config.txt; then
  echo "dtoverlay=dwc2" | sudo tee -a /boot/firmware/config.txt
fi

# 2. Install dependencies
# ------------------------------
# python3-venv        → needed to create a virtual environment (PEP 668 friendly)
# python3-pip         → pip inside the venv (we still upgrade pip in the venv)
# mosquitto-clients   → useful for testing MQTT (mosquitto_pub/sub)
# paho-mqtt (via pip) → Python MQTT client library used by mqtt_to_shield_hid.py
echo "Installing dependencies..."
sudo apt-get update
sudo apt-get install -y python3-venv python3-pip mosquitto-clients

echo "Creating Python venv at ${VENV} ..."
python3 -m venv "${VENV}"
"${VENV}/bin/pip" install --upgrade pip

echo "Installing Python dependencies into the venv..."
"${VENV}/bin/pip" install paho-mqtt


# 3. Install systemd service units
# ------------------------------
# systemd = init system that controls how services start on Linux.
# Units in /etc/systemd/system/ override or add to the distro defaults.
#
# Why this path matters:
#   - /usr/lib/systemd/system/ → packaged defaults from apt
#   - /etc/systemd/system/     → local admin overrides/additions (highest priority)
#
# By copying our *.service files into /etc/systemd/system/,
# we tell systemd: "treat these like first-class services".
#
# After placing them there, we use `systemctl enable` to:
#   - create symlinks in /etc/systemd/system/multi-user.target.wants/
#   - guarantee they’re started automatically at boot in multi-user mode.
#
# The two units are:
#   - hidg.service                 → one-time setup of /sys/kernel/config USB HID gadget (keyboard)
#   - mqtt_to_shield_hid.service  → long-running Python bridge, listens to MQTT & writes to /dev/hidg*
echo "Installing systemd service files..."
sudo cp "${DEVICE_DIR}/hidg.service"               /etc/systemd/system/
sudo cp "${DEVICE_DIR}/mqtt_to_shield_hid.service" /etc/systemd/system/

# 4. Enable and start services
# ------------------------------
# systemctl daemon-reexec   → tell systemd to reload and rescan new service files.
# systemctl enable <unit>   → enable the unit for autostart at boot.
# systemctl start <unit>    → start it immediately in this session.
#
# So after this step:
#   - On boot: kernel loads dwc2/libcomposite, systemd runs hidg.service, sets up HID gadget.
#   - Then mqtt_to_shield_hid.service starts and subscribes to MQTT, ready to inject key presses.
echo "Enabling and starting services..."
sudo systemctl daemon-reexec
sudo systemctl enable hidg.service
sudo systemctl enable mqtt_to_shield_hid.service
sudo systemctl start hidg.service
sudo systemctl start mqtt_to_shield_hid.service

echo "✅ Install complete. Reboot now to ensure gadget mode is active."
