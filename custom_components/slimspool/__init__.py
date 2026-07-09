"""Inicjalizacja integracji SlimSpool."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    CONF_ACTIVE_SPOOL_SENSOR,
    CONF_CONSUMPTION_SENSOR,
    CONF_CONSUMPTION_UNIT,
    DOMAIN,
    ENTRY_TYPE,
    TYPE_DEVICE,
    TYPE_SPOOL,
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

        # Słuchacz zmiany aktywnej szpuli (BEZPIECZNY ASYNC)
        if active_sensor and active_sensor != "Brak / Tylko lokalizacja":

            @callback
            def async_active_spool_changed(event: Event):
                """Wywoływane asynchronicznie przez pętlę zdarzeń HA."""
                hass.bus.async_fire("slimspool_relations_updated")

            entry.async_on_unload(
                async_track_state_change_event(
                    hass, [active_sensor], async_active_spool_changed
                )
            )

        # Słuchacz zużycia filamentu (BEZPIECZNY ASYNC)
        if consumption_sensor and consumption_sensor != "Brak / Tylko lokalizacja":

            @callback
            def async_consumption_changed(event):
                """Obsługa zmiany stanu sensora zużycia filamentu."""
                old_state = event.data.get("old_state")
                new_state = event.data.get("new_state")

                # Jeśli stany są nieważne lub niedostępne, ignoruj
                if (
                    old_state is None
                    or new_state is None
                    or old_state.state in ("unknown", "unavailable")
                    or new_state.state in ("unknown", "unavailable")
                ):
                    return

                try:
                    old_val = float(old_state.state)
                    new_val = float(new_state.state)

                    # Kluczowe zabezpieczenie:
                    if new_val < old_val:
                        # Sensor został zresetowany (nowy druk lub restart).
                        # Przyjmujemy, że od zera przybyło tyle, ile wynosi 'new_val'.
                        diff = new_val
                    else:
                        # Standardowy przyrost w trakcie jednego druku
                        diff = new_val - old_val

                    if diff <= 0:
                        return

                    # Pobieramy nazwę aktywnej szpuli z drugiego sensora
                    active_spool = "Brak"
                    active_spool_sensor = entry.data.get(CONF_ACTIVE_SPOOL_SENSOR)
                    if active_spool_sensor:
                        spool_state = hass.states.get(active_spool_sensor)
                        if spool_state:
                            active_spool = spool_state.state

                    # Jeśli mamy aktywną szpulę, odpalamy zdarzenie odejmowania w pętli HA
                    if active_spool and active_spool != "Brak / Tylko lokalizacja":
                        # POPRAWKA OSTRZEŻENIA Z LOGÓW: Używamy hass.loop.call_soon_threadsafe
                        # lub zwykłego hass.bus.async_fire bezpośrednio (bo jesteśmy w @callback w MainThread)
                        hass.bus.async_fire(
                            "slimspool_deduct_weight",
                            {
                                "spool_name": active_spool,
                                "amount": diff,
                                "unit": entry.data.get(CONF_CONSUMPTION_UNIT, "g")
                            }
                        )

                except ValueError:
                    # Ignoruj błędy konwersji tekstu na float
                    pass

            entry.async_on_unload(
                async_track_state_change_event(
                    hass, [consumption_sensor], async_consumption_changed
                )
            )

    # Nasłuchiwanie na wypadek edycji danych w locie
    entry.async_on_unload(entry.add_update_listener(async_update_listener))
    return True


async def async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Obsługa przeładowania po edycji w GUI."""
    await hass.config_entries.async_reload(
        entry.entry_entry_id if hasattr(entry, "entry_entry_id") else entry.entry_id
    )


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Usunięcie konfiguracji."""
    config = entry.data
    entry_type = config.get(ENTRY_TYPE)

    if entry_type == TYPE_SPOOL:
        return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    elif entry_type == TYPE_DEVICE:
        if entry.entry_id in hass.data[DOMAIN]["devices"]:
            del hass.data[DOMAIN]["devices"][entry.entry_id]
        # Wywołujemy odświeżenie pozycji, bo urządzenie zniknęło, szpula wraca na półkę
        hass.bus.async_fire("slimspool_relations_updated")
        return True
