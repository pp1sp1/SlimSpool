"""Obsługa formularza GUI i edycji dla SlimSpool."""

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import entity_registry as er

from .const import (
    AVAILABLE_COLORS,
    CONF_ACTIVE_SPOOL_SENSOR,
    CONF_COLOR,
    CONF_CONSUMPTION_SENSOR,
    CONF_CONSUMPTION_UNIT,
    CONF_DENSITY,
    CONF_DEVICE_TYPE,
    CONF_INITIAL_WEIGHT,
    CONF_MATERIAL,
    CONSUMPTION_UNITS,
    DOMAIN,
    ENTRY_TYPE,
    TYPE_DEVICE,
    TYPE_SPOOL,
    UNIT_GRAMS,
)


class SlimSpoolConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Klasa obsługująca dynamiczny przepływ konfiguracji z GUI."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Uruchomienie przepływu opcji (edycji) - Poprawny format dla klas potomnych."""
        return SlimSpoolOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        """Pierwszy krok: Wybór co użytkownik chce dodać."""
        if user_input is not None:
            if user_input[ENTRY_TYPE] == TYPE_SPOOL:
                return await self.async_step_spool()
            return await self.async_step_device()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(ENTRY_TYPE, default=TYPE_SPOOL): vol.In(
                        {
                            TYPE_SPOOL: "Dodaj nową szpulę filamentu",
                            TYPE_DEVICE: "Dodaj drukarkę lub suszarkę",
                        }
                    )
                }
            ),
        )

    async def async_step_spool(self, user_input=None):
        """Formularz dodawania szpuli."""
        if user_input is not None:
            user_input[ENTRY_TYPE] = TYPE_SPOOL
            unique_id = f"spool_{user_input['name'].lower().replace(' ', '_')}"
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=f"Szpula: {user_input['name']}", data=user_input
            )

        return self.async_show_form(
            step_id="spool",
            data_schema=vol.Schema(
                {
                    vol.Required("name"): str,
                    vol.Optional(CONF_MATERIAL, default="PLA"): str,
                    vol.Optional(CONF_COLOR, default="Czarny"): vol.In(
                        AVAILABLE_COLORS
                    ),
                    vol.Optional(CONF_INITIAL_WEIGHT, default=1000): int,
                    vol.Optional(CONF_DENSITY, default=1.24): float,
                }
            ),
        )

    async def async_step_device(self, user_input=None):
        """Formularz dodawania urządzenia (Drukarki/Suszarki)."""
        if user_input is not None:
            user_input[ENTRY_TYPE] = TYPE_DEVICE
            unique_id = f"device_{user_input['name'].lower().replace(' ', '_')}"
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=f"Urządzenie: {user_input['name']}", data=user_input
            )

        entity_reg = er.async_get(self.hass)
        all_sensors = ["Brak / Tylko lokalizacja"]
        for entity in entity_reg.entities.values():
            if entity.domain in ("sensor", "input_text", "select", "input_select"):
                all_sensors.append(entity.entity_id)

        return self.async_show_form(
            step_id="device",
            data_schema=vol.Schema(
                {
                    vol.Required("name"): str,
                    vol.Required(CONF_DEVICE_TYPE, default="Drukarka"): vol.In(
                        ["Drukarka", "Suszarka"]
                    ),
                    vol.Required(CONF_ACTIVE_SPOOL_SENSOR): vol.In(all_sensors),
                    vol.Optional(
                        CONF_CONSUMPTION_SENSOR, default="Brak / Tylko lokalizacja"
                    ): vol.In(all_sensors),
                    vol.Optional(CONF_CONSUMPTION_UNIT, default=UNIT_GRAMS): vol.In(
                        CONSUMPTION_UNITS
                    ),
                }
            ),
        )


class SlimSpoolOptionsFlowHandler(config_entries.OptionsFlow):
    """Klasyczny i stabilny handler edycji wpisów."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Inicjalizacja z jawnym przypisaniem wpisu (odporne na wersje HA)."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Wybór formularza edycji."""
        current_data = self.config_entry.data
        entry_type = current_data.get(ENTRY_TYPE)

        if user_input is not None:
            new_data = {**current_data, **user_input}
            self.hass.config_entries.async_update_entry(
                self.config_entry, data=new_data
            )
            return self.async_create_entry(title="", data={})

        entity_reg = er.async_get(self.hass)
        all_sensors = ["Brak / Tylko lokalizacja"]
        for entity in entity_reg.entities.values():
            if entity.domain in ("sensor", "input_text", "select", "input_select"):
                all_sensors.append(entity.entity_id)

        if entry_type == TYPE_SPOOL:
            return self.async_show_form(
                step_id="init",
                data_schema=vol.Schema(
                    {
                        vol.Optional(
                            CONF_MATERIAL,
                            default=current_data.get(CONF_MATERIAL, "PLA"),
                        ): str,
                        vol.Optional(
                            CONF_COLOR, default=current_data.get(CONF_COLOR, "Czarny")
                        ): vol.In(AVAILABLE_COLORS),
                        vol.Optional(
                            CONF_INITIAL_WEIGHT,
                            default=current_data.get(CONF_INITIAL_WEIGHT, 1000),
                        ): int,
                        vol.Optional(
                            CONF_DENSITY, default=current_data.get(CONF_DENSITY, 1.24)
                        ): float,
                    }
                ),
            )
        else:
            return self.async_show_form(
                step_id="init",
                data_schema=vol.Schema(
                    {
                        vol.Required(
                            CONF_ACTIVE_SPOOL_SENSOR,
                            default=current_data.get(
                                CONF_ACTIVE_SPOOL_SENSOR, "Brak / Tylko lokalizacja"
                            ),
                        ): vol.In(all_sensors),
                        vol.Optional(
                            CONF_CONSUMPTION_SENSOR,
                            default=current_data.get(
                                CONF_CONSUMPTION_SENSOR, "Brak / Tylko lokalizacja"
                            ),
                        ): vol.In(all_sensors),
                        vol.Optional(
                            CONF_CONSUMPTION_UNIT,
                            default=current_data.get(CONF_CONSUMPTION_UNIT, UNIT_GRAMS),
                        ): vol.In(CONSUMPTION_UNITS),
                    }
                ),
            )
