# BLE Wizard — browse, probe and adopt any BLE device from Home Assistant

A Home Assistant custom integration that adds a **BLE Wizard** panel to the
sidebar. It shows every Bluetooth device your adapters and ESPHome Bluetooth
proxies can see — decoded for humans — and lets you turn any readable GATT
characteristic into a sensor entity with one click.

## What you get

- **Device browser**: live table of all advertising BLE devices — name, MAC,
  manufacturer (company ID resolved to a name), RSSI, which proxy sees it,
  connectable or not, first/last seen. Advertisement payloads are shown as
  hex *and* ASCII *and* numbers, with standard service UUIDs resolved to
  their Bluetooth SIG names.
- **Probe**: for a connectable device, one click connects (via whichever proxy
  currently has the best link), walks the full GATT database and reads every
  readable characteristic. Standard characteristics (Battery Level, Device
  Information, Temperature, …) are decoded properly; unknown ones get
  best-guess interpretations (text / number / hex) you can choose from.
- **Add as sensor**: a button per characteristic creates the entity. The
  device is then polled on a configurable interval (default 5 min), reading
  all of its added characteristics in a single connection per poll —
  battery-friendly. Removing the last characteristic removes the device again.

## Install

1. Copy `custom_components/ble_wizard` into your HA config directory so you
   have `config/custom_components/ble_wizard/…` (or add this repo in HACS as
   a custom repository).
2. Make sure at least one ESPHome Bluetooth proxy has active connections on:
   ```yaml
   bluetooth_proxy:
     active: true
   ```
   (A local Bluetooth adapter on the HA host works too.)
3. Restart Home Assistant.
4. Settings → Devices & Services → Add Integration → **BLE Wizard**.
5. Open **BLE Wizard** in the sidebar (admin users only).

## Usage notes

- Click a row to expand it: advertised services and decoded advertisement
  data, plus the **Probe device** button.
- Probing connects to the device once. It can take up to 90 s on a weak link;
  if the device is battery powered it costs a little battery, so it's only
  ever done when you click.
- Known standard characteristics get proper units and device classes
  (battery %, °C, …). For unknown characteristics, pick how to decode from
  the dropdown (text / unsigned / signed / hex) before adding.
- Poll interval is per device: Settings → Devices & Services → BLE Wizard →
  the device's entry → **Configure**.
- If a device is out of range, its sensors show *unavailable* and recover on
  a later poll. A single failing characteristic shows *unknown* while the
  rest keep working.

## Debug logging

```yaml
logger:
  logs:
    custom_components.ble_wizard: debug
```

## Development / testing

There is no build step: the panel is one vanilla-JS module at
`custom_components/ble_wizard/frontend/panel.js` served by the integration.

A ready-to-use throwaway HA lives in [ha-test/](ha-test/):

```sh
cd ha-test && docker compose up -d
# http://localhost:8123 — admin / turbohmi-test-1234
```

Its config is already onboarded (admin user, BLE Wizard hub, ESPHome proxy
entry) and bind-mounts the integration from this repo, so code changes only
need a container restart (Python) or a browser reload (panel.js).

Docker containers have no Bluetooth of their own — the instance gets its
radio from an ESPHome Bluetooth proxy on your network (added via the ESPHome
integration by IP). Quirk: after a restart the proxy's scanner sometimes
stays idle; reload the ESPHome integration entry to kick it.

## Architecture (for the curious)

- `tracker.py` subscribes to *all* advertisements (passive, match-everything)
  and keeps per-device records; pushes debounced updates over a websocket
  subscription to the panel.
- `gatt.py` does the connecting: on-demand probe (full GATT walk) and the
  scheduled poll (one connection, all configured characteristics).
- `decoders.py` is the single source of truth for how bytes become values —
  shared by the probe UI and the sensors.
- Config entries: one hidden "hub" entry owns the panel/tracker/websocket
  API; one entry per adopted device stores its characteristic list
  (`entry.data`) and poll interval (`entry.options`). Changes reload the
  entry, which re-creates its sensors.
