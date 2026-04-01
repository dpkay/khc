# Home Assistant Configuration

Home Assistant OS runs in a UTM VM on the Mac Mini (192.168.1.20). This
directory is symlinked from the HAOS VM at `/config/`:

- `/config/configuration.yaml` -> this repo's `configuration.yaml`
- `/config/pyscript/` -> this repo's `pyscript/`
- `/config/www/` is NOT symlinked — it receives build output from `app/deploy.sh`

## Pyscript Architecture

Top-level files have `@mqtt_trigger`, `@state_trigger`, and `@service`
decorators that register with Home Assistant. Files in `modules/` are
importable libraries only — their decorators do NOT register automatically.

Workaround: triggers from modules are duplicated as top-level files on HAOS
(`/config/pyscript/tasmota_trigger.py`, `samsung_qn90a_trigger.py`). These
are not in the repo — they're created manually on HAOS.

### Files

- `main.py` — MQTT handler for the Macally numpad, Flic buttons
- `bedroom_soundmix.py` — DAW sound mix switching (5 modes), plug control
- `bedroom_kvm.py` — KVM source switching (4 inputs)
- `bedroom_desk_lights.py` — Z-Wave desk dimmer, rate-limited updates

### Modules

- `tasmota.py` — syncs input_boolean state to Tasmota switches
- `somfy_shades.py` — Z-Wave shade control (10 shades, 3 rooms)
- `livingroom_lights.py` — light scene presets (8 scenes)
- `nvidia_shield_tv.py` — Shield navigation, ADB commands, app launchers
- `samsung_qn90a.py` — TV ambient mode, power, HDMI source
- `denon_avr.py` — AVR volume control with caching
- `spotify.py` — Spotify playlist control (inactive)
- `kidsroom_luca_bed.py` — timed bed light (disabled, shares desk dimmer entity)

## www/

Build output from the React web remote app (`app/`). Deployed via
`app/deploy.sh`. Accessible at `http://192.168.1.20:8123/local/index.html`.

## Updating

On the Mac, edit files in this directory and they're live on HAOS via symlink.
After changes, restart HA: `ssh root@192.168.1.20 'ha core restart'`

Or from HAOS: `cd /config/khc && git pull`
