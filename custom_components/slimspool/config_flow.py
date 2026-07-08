"""Obsługa formularza GUI dla SlimSpool."""

import voluptuous as vol
from homeassistant import config_entries

from .const import CONF_COLOR, CONF_INITIAL_WEIGHT, CONF_MATERIAL, DOMAIN


class SlimSpoolConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Klasa obsługująca przepływ konfiguracji przez interfejs użytkownika."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Krok wywoływany przy dodawaniu nowej szpuli w GUI."""
        errors = {}

        if user_input is not None:
            # Unikalny identyfikator na podstawie nazwy szpuli
            unique_id = user_input["name"].lower().replace(" ", "_")
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(title=user_input["name"], data=user_input)

        # Formularz wyświetlany w interfejsie Home Assistant
        DATA_SCHEMA = vol.Schema(
            {
                vol.Required("name"): str,
                vol.Optional(CONF_MATERIAL, default="PLA"): str,
                vol.Optional(CONF_COLOR, default="Czarny"): str,
                vol.Optional(CONF_INITIAL_WEIGHT, default=1000): int,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )
