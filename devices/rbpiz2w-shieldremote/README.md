# rbpiz2w-shieldremote

USB HID “remote” for NVIDIA Shield driven by MQTT.
- Hardware: Raspberry Pi Zero 2 W (micro-USB “USB” port → Shield USB-A)
- Software: USB gadget (keyboard + consumer control) via configfs, Python MQTT bridge

## Prereqs (done once outside this bundle)
Edit the boot files on Raspberry Pi OS (new layout paths):
- `/boot/firmware/config.txt`: add this on its own line
```
dtoverlay=dwc2
```
- `/boot/firmware/cmdline.txt`: in the one long line, after `rootwait` add:
```
modules-load=dwc2
```

## Install
```bash
cd ~/khc/rbpiz2w-shieldremote
bash extract_files.sh setup_bundle.md
./install.sh
```

## MQTT topic & payload
- Topic: `kha/livingroom/shield/press_key`
- Payload: `{"name":"up|down|left|right|center|back|play_pause|next|prev|vol_up|vol_down"}`

## Notes
- If HOME doesn’t map from keyboard “Home,” you can add an ADB fallback later.
- Power draw: ~0.6–1.0 W (powered by the Shield’s USB).

