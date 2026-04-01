# Raspberry Pi 3 — Numpad to MQTT

Macally RF numpad bridge: reads key events via `evdev` and publishes to MQTT.
Runs as a systemd service, auto-starts on boot. No X11 or display required.

## Numpad Layout

The Macally RF numpad has 3 modifier keys (`0`=ALT, `.`=MUSIC, `Enter`=LIGHT)
and a 4x4 grid of action keys. Holding a modifier changes what every key does.
The pyscript handler is in `homeassistant/pyscript/main.py`.

### No modifier — Shield Remote + Volume
```
+----------+----------+----------+----------+
|  Prev    | Play/    |  Next    | Ambient  |
|          |  Pause   |          |  Mode    |
+----------+----------+----------+----------+
|          |    Up    |  Menu    |  Vol+    |
+----------+----------+----------+----------+
|   Left   |  Center  |  Right   |  Vol-    |
+----------+----------+----------+----------+
|   Back   |   Down   |   Home   |          |
+----------+----------+----------+----------+
```

### ALT modifier (hold 0) — Shades + Shield Apps + Volume Presets
```
+----------+----------+----------+----------+
| Shade L  | Shade R  | Shield   | TV Off   |
|    Up    |    Up    | Reboot   |          |
+----------+----------+----------+----------+
| Shade L  | Shade R  | Match    | Vol:     |
|   Stop   |   Stop   | Framerte |  High    |
+----------+----------+----------+----------+
| Shade L  | Shade R  |          | Vol:     |
|   Down   |   Down   |          |  Low     |
+----------+----------+----------+----------+
| Screen-  | Start    | Start    |          |
|  saver   |  Kodi    | YouTube  |          |
+----------+----------+----------+----------+
  Shades: livingroom solar (left/right only)
```

### LIGHT modifier (hold Enter) — Light Scenes
```
+----------+----------+----------+----------+
| All Off  |   Dim    |   Low    |          |
+----------+----------+----------+----------+
| All On   | Reading  | Dining   | LR Only  |
|          |          |          |   On     |
+----------+----------+----------+----------+
|          |          |          | LR Only  |
|          |          |          |   Dim    |
+----------+----------+----------+----------+
|          |          |          |          |
+----------+----------+----------+----------+
```

### MUSIC modifier (hold .) — Spotify Playlists
(Not currently active)

## Setup

```bash
cd ~/khc/python
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[rbpi3]'
```

Ensure `~/khc-private/.env` exists with MQTT credentials.

Add user to input group (for /dev/input access without root):
```bash
sudo usermod -a -G input $USER
```

Install and enable systemd service:
```bash
sudo cp ~/khc/devices/rbpi3/numpad_to_mqtt.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable numpad_to_mqtt.service
sudo systemctl start numpad_to_mqtt.service
```

## Troubleshooting

```bash
sudo systemctl status numpad_to_mqtt.service
sudo journalctl -u numpad_to_mqtt.service -f
```
