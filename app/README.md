# Kaeser-Chen Home Control — Web Remote

React/TypeScript PWA for controlling the home from a phone. Connects directly
to Home Assistant's websocket API. Served from HA's `/config/www/` directory.

## Tabs

- **Shield/TV** — D-pad navigation, media controls, volume slider, ambient mode,
  TV power, app launchers (Kodi, YouTube, Screensaver)
- **Lights** — Scene presets (All On, All Off, Dim, Low, Reading, Dining, etc.)
- **Shades** — Per-shade up/stop/down for all 10 Somfy shades, grouped by room

## Architecture

```
Phone Browser
    ↓ (WebSocket)
Home Assistant (192.168.1.20:8123)
    ↓ (pyscript / MQTT / service calls)
Devices (Shield, Denon, Lutron, Somfy, Tasmota)
```

The app calls HA services directly via websocket — no backend needed. Shield
navigation keys are published via MQTT (same as the physical numpad). Light
scenes and shade commands go through pyscript services.

## Development

```bash
npm install
npm run dev
```

Vite dev server proxies to HA. The HA access token is read from
`~/khc-private/.env` (`HA_TOKEN=...`) at build time via `vite.config.ts`.

## Deploy

```bash
./deploy.sh
```

Builds and scps to HAOS `/config/www/`. Accessible at
`http://192.168.1.20:8123/local/index.html`.

## Install as PWA

On Android Chrome: visit the URL → three dots → Install app.
Requires `chrome://flags/#unsafely-treat-insecure-origin-as-secure` set to
`http://192.168.1.20:8123` for fullscreen PWA mode (no HTTPS on local network).
