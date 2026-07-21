"""Config flow for BLE Wizard.

The user only ever adds the hub manually; device entries are created
programmatically by the websocket API via SOURCE_INTEGRATION_DISCOVERY when
"Add as sensor" is clicked in the panel.
"""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback

from .const import (
    CONF_ADDRESS,
    CONF_NAME,
    CONF_POLL_INTERVAL,
    DEFAULT_POLL_INTERVAL,
    DOMAIN,
    HUB_UNIQUE_ID,
)


class BLEWizardConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle config flows for both the hub and programmatic device entries."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Add the hub (single instance)."""
        await self.async_set_unique_id(HUB_UNIQUE_ID)
        self._abort_if_unique_id_configured()
        if user_input is not None:
            return self.async_create_entry(title="BLE Wizard", data={})
        return self.async_show_form(step_id="user")

    async def async_step_integration_discovery(
        self, discovery_info: dict[str, Any]
    ) -> ConfigFlowResult:
        """Create a device entry from the panel's add_characteristic command."""
        address = discovery_info[CONF_ADDRESS]
        await self.async_set_unique_id(address)
        self._abort_if_unique_id_configured()
        return self.async_create_entry(
            title=discovery_info.get(CONF_NAME) or address,
            data=discovery_info,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return BLEWizardOptionsFlow()


class BLEWizardOptionsFlow(OptionsFlow):
    """Poll interval for device entries; the hub has no options."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if CONF_ADDRESS not in self.config_entry.data:
            return self.async_abort(reason="no_options")
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = self.config_entry.options.get(
            CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL
        )
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_POLL_INTERVAL, default=current): vol.All(
                        vol.Coerce(int), vol.Range(min=30, max=86400)
                    )
                }
            ),
        )
