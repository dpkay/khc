# Kaeser-Chen Home Control (KHC)

Integrated home automation and studio control system. Bridges MQTT, Home
Assistant, MIDI controllers, and various devices across macOS, Linux, and
embedded hardware.

## Architecture

```
Phone (Web Remote)
    |
    v
Home Assistant (HAOS VM on Mac Mini, 192.168.1.20)
    |-- Pyscript automations (lights, shades, soundmix, TV, Shield)
    |-- Mosquitto MQTT broker
    |-- Z-Wave JS UI (Somfy shades, desk dimmer)
    |-- Lutron Caseta (lights)
    |-- Tasmota (smart plugs)
    |
    +-- Mac Mini services (via MQTT)
    |   |-- khc_mqtt_to_kvm (Level1Techs KVM via USB serial)
    |   |-- khc_mqtt_to_reaper (REAPER DAW via OSC)
    |   +-- khc_sparrow_to_mqtt (Sparrow 5x5 MIDI controller)
    |
    +-- Raspberry Pi 3 (via MQTT)
    |   +-- numpad_to_mqtt (Macally RF numpad via evdev)
    |
    +-- Raspberry Pi Zero 2W (via MQTT)
        +-- Shield HID bridge (USB keyboard emulation)
```

## Repository Structure

```
khc/
├── app/                    # React/TypeScript web remote (Vite PWA)
├── devices/
│   ├── mac_mini/           # LaunchAgent plists, REAPER session
│   ├── rbpi3/              # Numpad systemd service
│   └── rbpiz2w-shieldremote/  # Shield HID bridge setup
├── homeassistant/          # HA config (symlinked from HAOS VM)
│   ├── configuration.yaml
│   ├── pyscript/           # Automation scripts
│   └── www/                # Web remote build output
├── python/                 # Shared Python service package
│   └── src/khc/services/
│       ├── common.py       # MQTT + secrets helpers
│       ├── mac_mini/       # Mac services
│       ├── rbpi3/          # Numpad service
│       └── rbpiz2w-shieldremote/  # Shield HID service
└── TODO.md
```

## Setup

Each device has its own setup instructions:

- **Mac Mini**: [devices/mac_mini/README.md](devices/mac_mini/README.md)
- **Raspberry Pi 3**: [devices/rbpi3/README.md](devices/rbpi3/README.md)
- **Pi Zero 2W**: [devices/rbpiz2w-shieldremote/README.md](devices/rbpiz2w-shieldremote/README.md)
- **Web Remote**: [app/README.md](app/README.md)
- **Python Services**: [python/README.md](python/README.md)
- **Home Assistant**: [homeassistant/README.md](homeassistant/README.md)

## Secrets

All devices read credentials from `~/khc-private/.env` (separate private git repo):
```
MQTT_HOST=192.168.1.20
MQTT_PORT=1883
MQTT_USER=kaeserchen
MQTT_PASSWORD=...
HA_TOKEN=...
```
