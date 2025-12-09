"""Support for Bluetooth device tracking."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components import bluetooth
from homeassistant.components.bluetooth import (
    BluetoothScanningMode,
    BluetoothServiceInfoBleak,
)
from homeassistant.components.device_tracker import SourceType
from homeassistant.components.device_tracker.config_entry import ScannerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers import device_registry as dr

_LOGGER = logging.getLogger(__name__)

DOMAIN = "bluetooth_tracker"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Bluetooth Tracker device tracker based on a config entry."""
    _LOGGER.info("Setting up Bluetooth Tracker device tracker platform")

    # Dictionary to keep track of already added devices
    tracked_devices: dict[str, BluetoothTrackerEntity] = {}

    @callback
    def _async_process_bluetooth_event(
        service_info: BluetoothServiceInfoBleak,
    ) -> None:
        """Process Bluetooth advertisement events."""
        address = service_info.address
        
        # Check if we've already created an entity for this device
        if address not in tracked_devices:
            _LOGGER.info(
                "Discovered new Bluetooth device: %s (%s)",
                service_info.name or "Unknown",
                address,
            )
            entity = BluetoothTrackerEntity(service_info, entry)
            tracked_devices[address] = entity
            async_add_entities([entity])
        else:
            # Update existing entity
            tracked_devices[address].update_from_advertisement(service_info)

    # Register the callback to listen for all Bluetooth advertisements
    entry.async_on_unload(
        bluetooth.async_register_callback(
            hass,
            _async_process_bluetooth_event,
            None,  # Match all services
            BluetoothScanningMode.ACTIVE,
        )
    )


class BluetoothTrackerEntity(ScannerEntity):
    """Represent a Bluetooth device tracker entity."""

    _attr_has_entity_name = True
    _attr_name = None

    def __init__(
        self,
        service_info: BluetoothServiceInfoBleak,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the Bluetooth tracker entity."""
        self._service_info = service_info
        self._address = service_info.address
        self._attr_unique_id = f"{DOMAIN}_{self._address.replace(':', '_').lower()}"
        self._attr_is_connected = True
        self._rssi = service_info.rssi

        # Set device info
        self._attr_device_info = dr.DeviceInfo(
            identifiers={(DOMAIN, self._address)},
            name=service_info.name or f"Bluetooth Device {self._address}",
            connections={(dr.CONNECTION_BLUETOOTH, self._address)},
        )

    @property
    def source_type(self) -> SourceType:
        """Return the source type."""
        return SourceType.BLUETOOTH

    @property
    def is_connected(self) -> bool:
        """Return true if the device is connected."""
        return self._attr_is_connected

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        return {
            "address": self._address,
            "rssi": self._rssi,
            "name": self._service_info.name or "Unknown",
        }

    @callback
    def update_from_advertisement(
        self, service_info: BluetoothServiceInfoBleak
    ) -> None:
        """Update the entity from a Bluetooth advertisement."""
        self._service_info = service_info
        self._rssi = service_info.rssi
        self._attr_is_connected = True
        self.async_write_ha_state()
