# KHC Mac Mini Services

Python services that bridge **MQTT with devices/software** for the home studio setup. They run as individual LaunchAgents on macOS, auto-started at login.

Services:

- `khc_mqtt_to_kvm` — control Level1Techs KVM via MQTT + USB serial
- `khc_mqtt_to_reaper` — control REAPER (DAW) via MQTT + OSC
- `khc_sparrow_to_mqtt` — send MIDI fader/knob updates to MQTT

Shared code lives in `python/src/khc/services/common.py`.

---

## 1. One-time setup on a new Mac

### Install dependencies
```bash
brew install python3
```

### Create and install the Python venv
```bash
cd ~/khc/python
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
```

### Set up MQTT secrets
```bash
cd ~ && git clone git@github.com:dpkay/khc-private.git
```

### Install LaunchAgents
```bash
for svc in mqtt-to-kvm mqtt-to-reaper sparrow-to-mqtt; do
  ln -sf ~/khc/devices/mac_mini/com.khc.$svc.plist ~/Library/LaunchAgents/
  launchctl bootstrap gui/$UID ~/Library/LaunchAgents/com.khc.$svc.plist
done
```

---

## 2. Daily use

### Status
```bash
launchctl list | grep khc
```

### Logs
```bash
tail -f ~/Library/Logs/khc/*.log
```

### Restart a single service
```bash
launchctl kickstart -k gui/$UID/com.khc.mqtt-to-reaper
```

### Restart all
```bash
for svc in mqtt-to-kvm mqtt-to-reaper sparrow-to-mqtt; do
  launchctl kickstart -k gui/$UID/com.khc.$svc
done
```

### Stop/uninstall
```bash
for svc in mqtt-to-kvm mqtt-to-reaper sparrow-to-mqtt; do
  launchctl bootout gui/$UID/com.khc.$svc
  rm ~/Library/LaunchAgents/com.khc.$svc.plist
done
```

---

## 3. Repo layout

```
devices/mac_mini/
  com.khc.mqtt-to-kvm.plist       # LaunchAgent
  com.khc.mqtt-to-reaper.plist    # LaunchAgent
  com.khc.sparrow-to-mqtt.plist   # LaunchAgent
  README.md

python/src/khc/services/
  common.py                       # shared MQTT helpers, secrets loading
  mac_mini/
    khc_mqtt_to_kvm.py            # MQTT -> KVM (serial)
    khc_mqtt_to_reaper.py         # MQTT -> REAPER (OSC)
    khc_sparrow_to_mqtt.py        # MIDI -> MQTT
```

---

## 4. Development notes

- All services share `MQTT_TOPIC_PREFIX` in `common.py`.
- Secrets are read from `~/khc-private/.env` (not checked into git).
- Each LaunchAgent handles auto-start at login + restart on crash (`KeepAlive`).
- `ThrottleInterval` of 5 seconds prevents rapid restart loops.
- Logs go to `~/Library/Logs/khc/<service>.log` and `<service>.err.log`.
