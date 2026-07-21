"""Constants for the BLE Wizard integration."""

from __future__ import annotations

DOMAIN = "ble_wizard"
VERSION = "0.1.0"

# Device config entries (entry.data)
CONF_ADDRESS = "address"
CONF_NAME = "name"
CONF_CHARACTERISTICS = "characteristics"
# CharConfig dict keys inside CONF_CHARACTERISTICS
CONF_CHAR_UUID = "uuid"
CONF_CHAR_HANDLE = "handle"
CONF_CHAR_DECODER = "decoder"
CONF_CHAR_NAME = "name"

# Device config entries (entry.options)
CONF_POLL_INTERVAL = "poll_interval"
DEFAULT_POLL_INTERVAL = 300

# The hub entry has no address; it owns the panel/tracker/websocket API.
HUB_UNIQUE_ID = "ble_wizard_hub"

PANEL_URL_PATH = "ble-wizard"
FRONTEND_URL = "/ble_wizard_static"

PROBE_TIMEOUT = 90
CHAR_READ_TIMEOUT = 10

# hass.data[DOMAIN] keys
DATA_TRACKER = "tracker"
DATA_PROBE_LOCKS = "probe_locks"
DATA_WS_REGISTERED = "ws_registered"
