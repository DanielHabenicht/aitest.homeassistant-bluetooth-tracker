"""Polling coordinator for one added BLE device."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.components import bluetooth
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import CONF_CHAR_DECODER, CONF_CHAR_HANDLE, CONF_CHAR_UUID, DOMAIN
from .decoders import char_key, decode_value
from .gatt import async_read_configured

_LOGGER = logging.getLogger(__name__)


class BLEWizardCoordinator(DataUpdateCoordinator[dict[str, StateType]]):
    """Connects on a timer and reads all configured characteristics at once."""

    def __init__(
        self,
        hass: HomeAssistant,
        address: str,
        char_configs: list[dict],
        poll_interval: int,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN} {address}",
            update_interval=timedelta(seconds=poll_interval),
        )
        self.address = address
        self.char_configs = char_configs

    async def _async_update_data(self) -> dict[str, StateType]:
        ble_device = bluetooth.async_ble_device_from_address(
            self.hass, self.address, connectable=True
        )
        if ble_device is None:
            raise UpdateFailed(
                f"{self.address} is not in range of any Bluetooth adapter or proxy"
            )
        try:
            raw_values = await async_read_configured(ble_device, self.char_configs)
        except Exception as err:  # noqa: BLE001 - surface any bleak/GATT error
            raise UpdateFailed(
                f"Error communicating with {self.address}: {err}"
            ) from err

        data: dict[str, StateType] = {}
        for cfg in self.char_configs:
            key = char_key(cfg[CONF_CHAR_UUID], cfg.get(CONF_CHAR_HANDLE))
            raw = raw_values.get(key)
            data[key] = (
                decode_value(cfg[CONF_CHAR_DECODER], cfg[CONF_CHAR_UUID], raw)
                if raw is not None
                else None
            )
        _LOGGER.debug("Polled %s: %s", self.address, data)
        return data
