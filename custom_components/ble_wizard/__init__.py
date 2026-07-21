"""The BLE Wizard integration.

Two kinds of config entries share this domain:
- The hub entry (no address in data): owns the sidebar panel, the
  advertisement tracker and the websocket API.
- Device entries (address in data): one per BLE device the user added from
  the panel; each runs a polling coordinator over its configured
  characteristics.
"""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from . import panel, websocket
from .const import (
    CONF_ADDRESS,
    CONF_CHARACTERISTICS,
    CONF_POLL_INTERVAL,
    DATA_PROBE_LOCKS,
    DATA_TRACKER,
    DATA_WS_REGISTERED,
    DEFAULT_POLL_INTERVAL,
    DOMAIN,
)
from .coordinator import BLEWizardCoordinator
from .tracker import AdvertisementTracker

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

type BLEWizardConfigEntry = ConfigEntry[BLEWizardCoordinator | None]


def _is_hub(entry: ConfigEntry) -> bool:
    return CONF_ADDRESS not in entry.data


async def async_setup_entry(
    hass: HomeAssistant, entry: BLEWizardConfigEntry
) -> bool:
    """Set up a BLE Wizard entry (hub or device)."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    if _is_hub(entry):
        tracker = AdvertisementTracker(hass)
        tracker.async_start()
        domain_data[DATA_TRACKER] = tracker
        domain_data.setdefault(DATA_PROBE_LOCKS, {})
        entry.async_on_unload(tracker.async_stop)

        # Websocket commands cannot be unregistered; register exactly once
        # even across hub reloads.
        if not domain_data.get(DATA_WS_REGISTERED):
            websocket.async_register_commands(hass)
            domain_data[DATA_WS_REGISTERED] = True

        await panel.async_register(hass)
        entry.runtime_data = None
        return True

    # Device entry
    address = entry.data[CONF_ADDRESS]
    coordinator = BLEWizardCoordinator(
        hass,
        address=address,
        char_configs=entry.data.get(CONF_CHARACTERISTICS, []),
        poll_interval=entry.options.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL),
    )
    # Raises ConfigEntryNotReady when the device is out of range; HA retries.
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def _async_update_listener(
    hass: HomeAssistant, entry: BLEWizardConfigEntry
) -> None:
    """Reload on any change: options (poll interval) or data (characteristics)."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(
    hass: HomeAssistant, entry: BLEWizardConfigEntry
) -> bool:
    """Unload a BLE Wizard entry."""
    if _is_hub(entry):
        panel.async_remove(hass)
        hass.data.get(DOMAIN, {}).pop(DATA_TRACKER, None)
        return True
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
