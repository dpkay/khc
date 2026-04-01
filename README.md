# Kaeser-Chen Home Control (KHC)

Integrated home automation and studio control system for our apartment. What
started as a few smart plugs has grown into a system that ties together
lighting, motorized shades, a music production studio, a home theater, and
various input devices — all coordinated through MQTT and Home Assistant.

## What it controls

**Lights** — 14 Lutron Caseta dimmers across living room, dining room, kitchen,
hallway, foyer, bedroom, kids room, bathroom, and closet. Controlled via
8 preset scenes (all on, dim, low, reading, dining, etc.) from the numpad,
web remote, or Stream Deck.

**Shades** — 10 Somfy motorized shades (solar and blackout) across living room,
bedroom, and kids room, controlled via Z-Wave. Each shade has independent
up/stop/down with per-room "all" controls.

**Home theater** — Samsung QN90A 85" TV, Denon AVR X4700H receiver, and
NVIDIA Shield TV. The Shield is navigated via a Raspberry Pi Zero 2W that
emulates a USB keyboard (HID gadget), plus ADB for app launching. The TV
supports ambient mode toggling and the receiver has volume control with
caching for responsive numpad +/- buttons.

**Music production studio** — REAPER DAW on the Mac Mini, controlled via OSC.
A Sparrow 5x5 MIDI controller (5 faders + 5 dials) sends real-time mix
parameters through MQTT to Home Assistant, which routes them to REAPER based
on the active sound mix. Five mix modes (piano/desk seat, speakers/headphones)
manage physical speaker/headphone switching via Tasmota smart plugs, with
mute-during-transition to prevent audio pops.

**KVM** — Level1Techs 4-port KVM switch controlled via USB serial, switching
between personal Mac, personal Windows, corporate Mac, and corporate Windows.

**Smart plugs** — 9 Tasmota (Sonoff) plugs controlling speakers, LED strips,
studio light, computer monitor, laptop fan, NVIDIA Shield power, and
holiday lights.

**Flic buttons** — bedside buttons for raising bedroom shades and controlling
the kids room bed light.

## Input devices

- **Macally RF numpad** — 17-key wireless numpad with 3 modifier keys giving
  4 pages of functions. Connected via a Raspberry Pi 3 running evdev.
- **Elgato Stream Deck** — ~50 buttons calling Home Assistant services directly
  (sound mix selection, KVM switching, light scenes, etc.)
- **Web remote** — React PWA served from Home Assistant, accessible on any phone.
  Three tabs: Shield/TV remote, lights, shades.
- **Sparrow 5x5** — MIDI fader/knob controller for real-time DAW parameter control.

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

Home Assistant OS runs in a UTM virtual machine on the Mac Mini. Everything
communicates over MQTT through a Mosquitto broker running as a HAOS add-on.
Python services on the Mac handle device-specific protocols (USB serial for
KVM, OSC for REAPER, MIDI for the Sparrow controller). The Raspberry Pis are
single-purpose appliances that bridge physical input devices to MQTT.

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
