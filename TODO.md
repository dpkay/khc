# KHC — Remaining Work

## 1. Flic buttons

HA logs show "Failed to connect to flic server". The Flic integration needs
a daemon running somewhere to bridge Bluetooth button presses to the network.

### Tasks
- Determine where the Flic daemon ran before (the old Pi? a dedicated Flic hub?)
- Either:
  - Run the Flic daemon on the Pi 3 (alongside numpad)
  - Run it on the Mac Mini
  - Use a Flic Hub LR if available
- Test the `on_flic_message_received` handler in `main.py` (DominikBed shades,
  LucaBed light)


## 2. Offline Tasmota devices

3 Tasmota devices (001, 002, 004) are offline and still point to the old
MQTT broker at 192.168.1.11. When powered on, update with:
```
curl -s "http://<ip>/cm?cmnd=MqttHost%20192.168.1.20"
```
- 001 — livingroom xmas lights
- 002 — diningroom xmas lights
- 004 — bedroom piano LED strip


## 3. Kidsroom Luca bed light

`kidsroom_luca_bed.py` timer is disabled because it shares the desk dimmer
entity (`light.bedroom_dimmer_desk_lights_dimmer`). Needs its own Z-Wave
dimmer or a different entity before re-enabling.


## 4. Pyscript trigger workaround

`tasmota_trigger.py` and `samsung_qn90a_trigger.py` in top-level pyscript
are workarounds for pyscript not registering `@state_trigger` from `modules/`.
If pyscript ever fixes this, these files can be removed and the triggers
moved back into the modules.


## 5. Pi 3 — remaining cleanup

- Give the Pi a memorable static IP? Currently `.11`.
- Fully remove Docker or just leave it disabled?
- Create `devices/rbpi3/install.sh` setup script (similar to Pi Zero's)
- Pi Zero's `khc_mqtt_to_shield_hid.py` should also use `common.py`
  for MQTT instead of reading env vars directly


## 6. Web remote app

- PWA fullscreen doesn't work over HTTP (needs HTTPS or Chrome flag)
- Old `homeassistant/www/remote.html` (single-file version) can be removed
  once the React app is fully verified
