# Home Assistant Configuration

Home Assistant OS runs in a UTM VM on the Mac Mini (192.168.1.20). HA reads
its config from `/homeassistant/` (aka `/config/`), where this repo's files
appear via symlinks into a HAOS-side git checkout at `/homeassistant/khc`:

- `/homeassistant/configuration.yaml` -> `/config/khc/homeassistant/configuration.yaml`
- `/homeassistant/pyscript/` -> `/config/khc/homeassistant/pyscript`
- `/homeassistant/www/` is NOT a symlink — it receives build output from `app/deploy.sh`

See "Updating" below for how to edit those files from the Mac.

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

Two git checkouts exist: this one on the Mac (`~/khc`) and one on HAOS at
`/homeassistant/khc`. The files HA actually reads are symlinks into the HAOS
checkout (`/homeassistant/configuration.yaml -> /config/khc/homeassistant/configuration.yaml`,
same for `pyscript/`). Sync the two checkouts via git push/pull.

After config changes: `ssh root@192.168.1.20 'ha core restart'` (pyscript
autoreloads on file change — restart only needed for `configuration.yaml`).

### Editing the HAOS checkout directly via SMB

For quick test edits without git round-tripping, mount HAOS's `/homeassistant`
as an SMB share. The Samba add-on must be installed in HA (user: `dpkay`,
password set in add-on config). Seed the macOS Keychain once by mounting via
Finder (`Cmd-K` → `smb://192.168.1.20` → check "Remember password").

Then mount at the canonical path:

```
mount_smbfs "//dpkay:$(security find-internet-password -s 192.168.1.20 -a dpkay -w)@192.168.1.20/config" /Volumes/homeassistant/config
```

(`/Volumes/homeassistant/` is a regular dir owned by the user; `config/` inside
is the mount point. Add sibling mounts for `addons`, `share`, etc. the same
way if needed.)

Edit at `/Volumes/homeassistant/config/khc/homeassistant/...` — changes are
live in HA. The top-level `configuration.yaml` and `pyscript` symlinks under
`/Volumes/homeassistant/config/` are not visible through SMB (absolute symlink
targets fall outside the share root); always edit through the `khc/` subtree
where the real files live. Commit from HAOS via SSH, then pull on the Mac
local repo to stay in sync.
