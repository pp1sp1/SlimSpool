import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import CONF_COLOR, CONF_INITIAL_WEIGHT, CONF_MATERIAL, DOMAIN


class FilamentManagerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Obsługa formularza GUI do dodawania szpuli."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Krok wywoływany, gdy użytkownik dodaje nową szpulę w GUI."""
        errors = {}

        if user_input is not None:
            # Unikalny ID na podstawie nazwy szpuli, żeby nie dodać dwóch takich samych
            unique_id = user_input["name"].lower().replace(" ", "_")
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(title=user_input["name"], data=user_input)

        # Definicja pól formularza w GUI
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
