# KHC Services

This repo contains small Python services that bridge **MQTT ↔ devices/software** for my home studio setup. They run in the background on macOS inside a `tmux` session, auto-started at login by a LaunchAgent.

Services:

- `khc-mqtt-to-kvm` → control Level1Techs KVM via MQTT + USB serial  
- `khc-mqtt-to-reaper` → control REAPER (DAW) via MQTT + OSC  
- `khc-sparrow-to-mqtt` → send MIDI fader/knob updates to MQTT  

Shared code lives in `services/common.py`.

---

## 1. One-time setup on a new Mac

### Install dependencies
```bash
# Xcode command line tools (if not installed already)
xcode-select --install

# Homebrew (if not installed already)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Core tools
brew install tmux python3

# Python deps
pip3 install paho-mqtt python-osc mido pyserial
```

### Set up MQTT secrets in **Keychain**
We never store secrets in `.env` files or the repo. Instead, store them once in macOS Keychain:

```bash
security add-generic-password -a "$USER" -s khc:MQTT_HOST -w 'your-broker.example.com'
security add-generic-password -a "$USER" -s khc:MQTT_USER -w 'your-username'
security add-generic-password -a "$USER" -s khc:MQTT_PASSWORD -w 'your-password'
```

Verify later:
```bash
security find-generic-password -s khc:MQTT_HOST -w
```

### Create logs dir
```bash
mkdir -p ~/Library/Logs/khc_services
```

### Install LaunchAgent
Symlink the LaunchAgent plist into `~/Library/LaunchAgents` (macOS only scans there):

```bash
ln -sf ~/khc/mac/com.khc.services.plist ~/Library/LaunchAgents/com.khc.services.plist
```

Register it with launchd (modern commands):

```bash
launchctl bootstrap gui/$UID ~/Library/LaunchAgents/com.khc.services.plist
launchctl enable gui/$UID/com.khc.services
launchctl kickstart -k gui/$UID/com.khc.services
```

---

## 2. Daily use

### Status
```bash
launchctl print gui/$UID/com.khc.services   # LaunchAgent status
tmux ls                                      # Session list (should show "khc")
```

### Attach to tmux
```bash
tmux attach -t khc
# (Ctrl-b then d to detach and leave it running)
```

### Logs
```bash
tail -f ~/Library/Logs/khc_services/*.log
```
- `khc-mqtt-to-kvm.log`  
- `khc-mqtt-to-reaper.log`  
- `khc-sparrow-to-mqtt.log`  
- `launchagent.out.log` / `launchagent.err.log`

### Restart everything
```bash
launchctl kickstart -k gui/$UID/com.khc.services
```

### Stop/uninstall
```bash
launchctl bootout gui/$UID/com.khc.services
rm ~/Library/LaunchAgents/com.khc.services.plist
```

---

## 3. Repo layout

```
khc/mac/
  services/
    common.py                # shared helpers
    khc-mqtt-to-kvm.py       # MQTT → KVM (serial)
    khc-mqtt-to-reaper.py    # MQTT → REAPER (OSC)
    khc-sparrow-to-mqtt.py   # MIDI → MQTT
  start_khc_services.py      # tmux launcher (manual use)
  com.khc.services.plist     # LaunchAgent for auto-start
  README.md
```

---

## 4. Development notes

- All services share `MQTT_TOPIC_PREFIX` in `common.py`. Change it there only.  
- Services read `MQTT_HOST`, `MQTT_USER`, `MQTT_PASSWORD` **only** from Keychain.  
- LaunchAgent handles auto-start at login + restart on crash (`KeepAlive`).  
- `tmux` allows manual inspection / restart of individual windows.  

---

## 5. New Mac quick checklist

1. Install Xcode CLT + Homebrew.  
2. `brew install tmux python3`  
3. `pip3 install paho-mqtt python-osc mido pyserial`  
4. Add MQTT secrets to Keychain (`security add-generic-password …`).  
5. `mkdir -p ~/Library/Logs/khc_services`  
6. `ln -sf ~/khc/mac/com.khc.services.plist ~/Library/LaunchAgents/com.khc.services.plist`  
7. `launchctl bootstrap gui/$UID ~/Library/LaunchAgents/com.khc.services.plist`  
8. `launchctl enable gui/$UID/com.khc.services`  
9. `launchctl kickstart -k gui/$UID/com.khc.services`  

Done ✅ — services will run automatically at each login.
