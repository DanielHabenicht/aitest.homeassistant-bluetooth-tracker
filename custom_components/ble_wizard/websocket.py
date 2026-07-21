"""Websocket API: the contract between the panel and the backend."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.config_entries import SOURCE_INTEGRATION_DISCOVERY
from homeassistant.core import HomeAssistant, callback

from .const import (
    CONF_ADDRESS,
    CONF_CHAR_DECODER,
    CONF_CHAR_HANDLE,
    CONF_CHAR_NAME,
    CONF_CHAR_UUID,
    CONF_CHARACTERISTICS,
    CONF_NAME,
    DATA_PROBE_LOCKS,
    DATA_TRACKER,
    DOMAIN,
)
from .decoders import DECODER_KNOWN, GENERIC_DECODER_KINDS
from .gatt import ProbeError, async_probe_device

_LOGGER = logging.getLogger(__name__)

VALID_DECODERS = (DECODER_KNOWN, *GENERIC_DECODER_KINDS)


@callback
def async_register_commands(hass: HomeAssistant) -> None:
    websocket_api.async_register_command(hass, ws_subscribe_advertisements)
    websocket_api.async_register_command(hass, ws_probe)
    websocket_api.async_register_command(hass, ws_add_characteristic)
    websocket_api.async_register_command(hass, ws_remove_characteristic)


def _tracker(hass: HomeAssistant):
    return hass.data.get(DOMAIN, {}).get(DATA_TRACKER)


def _device_entry(hass: HomeAssistant, address: str):
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.data.get(CONF_ADDRESS) == address:
            return entry
    return None


@websocket_api.require_admin
@websocket_api.websocket_command(
    {vol.Required("type"): "ble_wizard/subscribe_advertisements"}
)
@callback
def ws_subscribe_advertisements(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Push the current device table, then debounced updates."""
    tracker = _tracker(hass)
    if tracker is None:
        connection.send_error(
            msg["id"], "hub_not_ready", "BLE Wizard hub is not set up"
        )
        return

    msg_id = msg["id"]

    @callback
    def _push(changed: list[dict]) -> None:
        connection.send_event(msg_id, {"devices": changed})

    connection.subscriptions[msg_id] = tracker.async_subscribe(_push)
    connection.send_result(msg_id)
    connection.send_event(msg_id, {"devices": tracker.snapshot(), "initial": True})


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): "ble_wizard/probe",
        vol.Required("address"): str,
    }
)
@websocket_api.async_response
async def ws_probe(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Connect to a device and return its full GATT map."""
    address = msg["address"]
    locks: dict[str, asyncio.Lock] = hass.data.setdefault(DOMAIN, {}).setdefault(
        DATA_PROBE_LOCKS, {}
    )
    lock = locks.setdefault(address, asyncio.Lock())
    if lock.locked():
        connection.send_error(
            msg["id"], "probe_in_progress", f"A probe of {address} is already running"
        )
        return
    async with lock:
        try:
            result = await async_probe_device(hass, address)
        except ProbeError as err:
            connection.send_error(msg["id"], err.code, str(err))
            return
    connection.send_result(msg["id"], result)


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): "ble_wizard/add_characteristic",
        vol.Required("address"): str,
        vol.Required("char_uuid"): str,
        vol.Required("decoder"): vol.In(VALID_DECODERS),
        vol.Required("name"): str,
        vol.Optional("char_handle"): vol.Any(int, None),
    }
)
@websocket_api.async_response
async def ws_add_characteristic(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Add (or update) a characteristic as a sensor on a device entry."""
    address = msg["address"]
    char_config = {
        CONF_CHAR_UUID: msg["char_uuid"],
        CONF_CHAR_HANDLE: msg.get("char_handle"),
        CONF_CHAR_DECODER: msg["decoder"],
        CONF_CHAR_NAME: msg["name"],
    }

    if (entry := _device_entry(hass, address)) is not None:
        chars = [
            c
            for c in entry.data.get(CONF_CHARACTERISTICS, [])
            if not (
                c[CONF_CHAR_UUID] == char_config[CONF_CHAR_UUID]
                and c.get(CONF_CHAR_HANDLE) == char_config[CONF_CHAR_HANDLE]
            )
        ]
        chars.append(char_config)
        hass.config_entries.async_update_entry(
            entry, data={**entry.data, CONF_CHARACTERISTICS: chars}
        )
        connection.send_result(
            msg["id"], {"entry_id": entry.entry_id, "created": False}
        )
        return

    tracker = _tracker(hass)
    record = tracker.devices.get(address) if tracker else None
    device_name = record.name if record else None
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_INTEGRATION_DISCOVERY},
        data={
            CONF_ADDRESS: address,
            CONF_NAME: device_name,
            CONF_CHARACTERISTICS: [char_config],
        },
    )
    if result.get("type") != "create_entry":
        connection.send_error(
            msg["id"],
            "add_failed",
            f"Could not create entry for {address}: {result.get('reason')}",
        )
        return
    connection.send_result(
        msg["id"], {"entry_id": result["result"].entry_id, "created": True}
    )


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): "ble_wizard/remove_characteristic",
        vol.Required("address"): str,
        vol.Required("char_uuid"): str,
        vol.Optional("char_handle"): vol.Any(int, None),
    }
)
@websocket_api.async_response
async def ws_remove_characteristic(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Remove a characteristic; removing the last one removes the entry."""
    address = msg["address"]
    entry = _device_entry(hass, address)
    if entry is None:
        connection.send_error(
            msg["id"], "not_found", f"No BLE Wizard entry for {address}"
        )
        return
    chars = [
        c
        for c in entry.data.get(CONF_CHARACTERISTICS, [])
        if not (
            c[CONF_CHAR_UUID] == msg["char_uuid"]
            and c.get(CONF_CHAR_HANDLE) == msg.get("char_handle")
        )
    ]
    if chars:
        hass.config_entries.async_update_entry(
            entry, data={**entry.data, CONF_CHARACTERISTICS: chars}
        )
        connection.send_result(msg["id"], {"removed": True, "entry_removed": False})
        return
    await hass.config_entries.async_remove(entry.entry_id)
    connection.send_result(msg["id"], {"removed": True, "entry_removed": True})
