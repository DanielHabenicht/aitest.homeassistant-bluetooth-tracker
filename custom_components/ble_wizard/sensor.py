"""Sensor platform: one entity per configured characteristic."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import BLEWizardConfigEntry
from .const import CONF_ADDRESS, CONF_CHARACTERISTICS, CONF_NAME
from .coordinator import BLEWizardCoordinator
from .decoders import build_entity_description


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BLEWizardConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    address = entry.data[CONF_ADDRESS]
    device_name = entry.data.get(CONF_NAME) or address
    descriptions = [
        build_entity_description(cfg)
        for cfg in entry.data.get(CONF_CHARACTERISTICS, [])
    ]

    # Prune entities for characteristics that were removed from the entry.
    wanted_unique_ids = {f"{address}_{d.key}" for d in descriptions}
    registry = er.async_get(hass)
    for reg_entry in er.async_entries_for_config_entry(registry, entry.entry_id):
        if reg_entry.unique_id not in wanted_unique_ids:
            registry.async_remove(reg_entry.entity_id)

    async_add_entities(
        BLEWizardSensor(coordinator, address, device_name, description)
        for description in descriptions
    )


class BLEWizardSensor(CoordinatorEntity[BLEWizardCoordinator], SensorEntity):
    """One characteristic read from the device on each poll."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: BLEWizardCoordinator,
        address: str,
        device_name: str,
        description: SensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{address}_{description.key}"
        self._attr_device_info = DeviceInfo(
            connections={(CONNECTION_BLUETOOTH, address)},
            name=device_name,
        )

    @property
    def native_value(self) -> StateType:
        # None here renders as "unknown" while the device itself stays
        # available — deliberately distinct from out-of-range (coordinator
        # failure -> unavailable via CoordinatorEntity.available).
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self.entity_description.key)
