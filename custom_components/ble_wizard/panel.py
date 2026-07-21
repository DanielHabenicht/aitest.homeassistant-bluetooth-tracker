"""Sidebar panel registration for BLE Wizard."""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components import frontend, panel_custom
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant, callback

from .const import FRONTEND_URL, PANEL_URL_PATH, VERSION

_LOGGER = logging.getLogger(__name__)


async def async_register(hass: HomeAssistant) -> None:
    """Serve the frontend module and add the sidebar panel."""
    await hass.http.async_register_static_paths(
        [
            StaticPathConfig(
                FRONTEND_URL,
                str(Path(__file__).parent / "frontend"),
                cache_headers=False,
            )
        ]
    )
    # Re-registering after a hub reload raises unless we remove first.
    async_remove(hass)
    await panel_custom.async_register_panel(
        hass=hass,
        frontend_url_path=PANEL_URL_PATH,
        webcomponent_name="ble-wizard-panel",
        sidebar_title="BLE Wizard",
        sidebar_icon="mdi:bluetooth-search",
        module_url=f"{FRONTEND_URL}/panel.js?v={VERSION}",
        require_admin=True,
    )


@callback
def async_remove(hass: HomeAssistant) -> None:
    if PANEL_URL_PATH in hass.data.get(frontend.DATA_PANELS, {}):
        frontend.async_remove_panel(hass, PANEL_URL_PATH)
