"""GATT I/O: on-demand probing and scheduled polling.

Free of entity/panel concerns; everything here takes an address or BLEDevice
and returns plain data.
"""

from __future__ import annotations

import asyncio
import logging

from bleak import BleakClient
from bleak.backends.device import BLEDevice
from bleak_retry_connector import establish_connection
from homeassistant.components import bluetooth
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import (
    CHAR_READ_TIMEOUT,
    CONF_ADDRESS,
    CONF_CHAR_HANDLE,
    CONF_CHAR_UUID,
    CONF_CHARACTERISTICS,
    DATA_TRACKER,
    DOMAIN,
    PROBE_TIMEOUT,
)
from .decoders import (
    KNOWN_CHARACTERISTICS,
    char_key,
    decode_candidates,
    suggested_decoder,
    uuid_name,
)

_LOGGER = logging.getLogger(__name__)


class ProbeError(HomeAssistantError):
    """A probe failed; `code` is a stable identifier for the frontend."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _resolve_ble_device(hass: HomeAssistant, address: str) -> BLEDevice:
    ble_device = bluetooth.async_ble_device_from_address(
        hass, address, connectable=True
    )
    if ble_device is not None:
        return ble_device
    tracker = hass.data.get(DOMAIN, {}).get(DATA_TRACKER)
    record = tracker.devices.get(address) if tracker else None
    if record is not None and not record.connectable:
        raise ProbeError(
            "not_connectable",
            f"{address} does not accept connections (advertisement-only device)",
        )
    raise ProbeError(
        "not_in_range",
        f"{address} is not in range of any Bluetooth adapter or proxy",
    )


async def async_probe_device(hass: HomeAssistant, address: str) -> dict:
    """Connect once and map the full GATT database, reading what we can."""
    ble_device = _resolve_ble_device(hass, address)
    try:
        async with asyncio.timeout(PROBE_TIMEOUT):
            return await _probe(hass, ble_device)
    except TimeoutError as err:
        raise ProbeError("timeout", f"Probe of {address} timed out") from err
    except ProbeError:
        raise
    except Exception as err:  # noqa: BLE001 - bleak raises many exception types
        raise ProbeError("connect_failed", str(err)) from err


async def _probe(hass: HomeAssistant, ble_device: BLEDevice) -> dict:
    address = ble_device.address
    added_keys = _added_char_keys(hass, address)
    client: BleakClient = await establish_connection(
        BleakClient, ble_device, address
    )
    services = []
    try:
        for service in client.services:
            characteristics = []
            for char in service.characteristics:
                readable = "read" in char.properties
                value: dict | None = None
                if readable:
                    value = await _read_char_for_probe(client, char)
                characteristics.append(
                    {
                        "uuid": char.uuid,
                        "name": uuid_name(char.uuid),
                        "handle": char.handle,
                        "properties": list(char.properties),
                        "readable": readable,
                        "value": value,
                        "suggested_decoder": (
                            suggested_decoder(char.uuid, bytes.fromhex(value["hex"]))
                            if value and value.get("hex") is not None
                            else None
                        ),
                        "added": char_key(char.uuid, char.handle) in added_keys,
                    }
                )
            services.append(
                {
                    "uuid": service.uuid,
                    "name": uuid_name(service.uuid),
                    "handle": service.handle,
                    "characteristics": characteristics,
                }
            )
    finally:
        await client.disconnect()
    return {"address": address, "services": services}


async def _read_char_for_probe(client: BleakClient, char) -> dict:
    """Read one characteristic; failures become data, not exceptions."""
    try:
        async with asyncio.timeout(CHAR_READ_TIMEOUT):
            raw = bytes(await client.read_gatt_char(char))
    except Exception as err:  # noqa: BLE001
        _LOGGER.debug("Probe read of %s failed: %s", char.uuid, err)
        return {"hex": None, "known": None, "candidates": [], "error": str(err)}
    known = None
    if (known_char := KNOWN_CHARACTERISTICS.get(char.uuid)) is not None:
        try:
            known = {"value": known_char.decode(raw), "unit": known_char.unit}
        except (ValueError, IndexError, UnicodeDecodeError):
            known = None
    return {
        "hex": raw.hex(),
        "known": known,
        "candidates": decode_candidates(raw),
        "error": None,
    }


def _added_char_keys(hass: HomeAssistant, address: str) -> set[str]:
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.data.get(CONF_ADDRESS) == address:
            return {
                char_key(c[CONF_CHAR_UUID], c.get(CONF_CHAR_HANDLE))
                for c in entry.data.get(CONF_CHARACTERISTICS, [])
            }
    return set()


async def async_read_configured(
    ble_device: BLEDevice, char_configs: list[dict]
) -> dict[str, bytes | None]:
    """Poll path: one connection, read every configured characteristic."""
    client: BleakClient = await establish_connection(
        BleakClient, ble_device, ble_device.address
    )
    results: dict[str, bytes | None] = {}
    try:
        for cfg in char_configs:
            uuid = cfg[CONF_CHAR_UUID]
            handle = cfg.get(CONF_CHAR_HANDLE)
            key = char_key(uuid, handle)
            target = None
            if handle is not None:
                target = client.services.get_characteristic(handle)
            if target is None:
                target = uuid
            try:
                async with asyncio.timeout(CHAR_READ_TIMEOUT):
                    results[key] = bytes(await client.read_gatt_char(target))
            except Exception as err:  # noqa: BLE001
                _LOGGER.warning(
                    "Reading %s on %s failed: %s", uuid, ble_device.address, err
                )
                results[key] = None
    finally:
        await client.disconnect()
    return results
