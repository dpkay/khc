# Raspberry Pi Zero 2W — Shield HID Remote

USB HID "remote" for NVIDIA Shield driven by MQTT.
- Hardware: Raspberry Pi Zero 2 W (micro-USB "USB" port -> Shield USB-A)
- Software: USB gadget (keyboard + consumer control) via configfs, Python MQTT bridge
- Power draw: ~0.6-1.0 W (powered by the Shield's USB)

## Supported Keys

Topic: `kha/livingroom/shield/press_key`
Payload: `{"name": "<key>"}`

Keys: `up`, `down`, `left`, `right`, `center`, `back`, `play_pause`, `next`,
`prev`, `vol_up`, `vol_down`

Note: `home` is not supported via HID — use the ADB integration instead
(`nvidia_shield_tv.home()` in pyscript).

## Setup

### Prerequisites

Edit the boot files on Raspberry Pi OS:

`/boot/firmware/config.txt` — add on its own line:
```
dtoverlay=dwc2
```

`/boot/firmware/cmdline.txt` — after `rootwait` add:
```
modules-load=dwc2
```

### Install

```bash
cd ~/khc/devices/rbpiz2w-shieldremote
./install.sh
```

This sets up the USB HID gadget, installs the Python venv, and enables the
systemd services (`hidg.service` and `mqtt_to_shield_hid.service`).

Create `~/khc-private/.env` with MQTT credentials (see top-level README).

### Verify

```bash
sudo systemctl status mqtt_to_shield_hid.service
sudo journalctl -u mqtt_to_shield_hid.service -f
```
