"""Inicjalizacja integracji SlimSpool."""

import logging
import math

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import Event, HomeAssistant
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    CONF_ACTIVE_SPOOL_SENSOR,
    CONF_CONSUMPTION_SENSOR,
    CONF_CONSUMPTION_UNIT,
    DOMAIN,
    ENTRY_TYPE,
    TYPE_DEVICE,
    TYPE_SPOOL,
    UNIT_MM,
    UNIT_MM3,
)

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.NUMBER]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Konfiguracja wpisu (Szpula lub Urządzenie)."""
    hass.data.setdefault(DOMAIN, {"spools": {}, "devices": {}})

    config = entry.data
    entry_type = config.get(ENTRY_TYPE)

    if entry_type == TYPE_SPOOL:
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    elif entry_type == TYPE_DEVICE:
        device_name = config.get("name")
        active_sensor = config.get(CONF_ACTIVE_SPOOL_SENSOR)
        consumption_sensor = config.get(CONF_CONSUMPTION_SENSOR)
        unit = config.get(CONF_CONSUMPTION_UNIT)

        hass.data[DOMAIN]["devices"][entry.entry_id] = {
            "name": device_name,
            "active_sensor": active_sensor,
            "consumption_sensor": consumption_sensor,
            "unit": unit,
        }

        if active_sensor and active_sensor != "Brak / Tylko lokalizacja":

            def async_active_spool_changed(event: Event):
                if event.data.get("new_state"):
                    hass.bus.async_fire("slimspool_relations_updated")

            entry.async_on_unload(
                async_track_state_change_event(
                    hass, [active_sensor], async_active_spool_changed
                )
            )

        if consumption_sensor and consumption_sensor != "Brak / Tylko lokalizacja":

            def async_consumption_changed(event: Event):
                new_state = event.data.get("new_state")
                old_state = event.data.get("old_state")
                if (
                    not new_state
                    or not old_state
                    or new_state.state in (None, "unknown", "unavailable")
                ):
                    return

                try:
                    active_spool_name = (
                        hass.states.get(active_sensor).state if active_sensor else None
                    )
                    if not active_spool_name:
                        return

                    raw_diff = float(new_state.state) - float(old_state.state)
                    if old_state.state == "0":
                        raw_diff = float(new_state.state)

                    if raw_diff > 0:
                        # Przekazujemy surową różnicę oraz jednostkę do szpuli,
                        # ponieważ to szpula zna swoją własną gęstość potrzebną do przeliczenia
                        hass.bus.async_fire(
                            "slimspool_deduct_weight",
                            {
                                "spool_name": active_spool_name,
                                "amount": raw_diff,
                                "unit": unit,
                            },
                        )
                except ValueError:
                    pass

            entry.async_on_unload(
                async_track_state_change_event(
                    hass, [consumption_sensor], async_consumption_changed
                )
            )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Usunięcie konfiguracji."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
