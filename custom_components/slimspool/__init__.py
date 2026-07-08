"""Inicjalizacja integracji SlimSpool."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Konfiguracja wpisu dodanego z poziomu GUI."""
    hass.data.setdefault(DOMAIN, {})

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Rejestracja globalnej usługi do odejmowania wagi (jeśli jeszcze nie istnieje)
    if not hass.services.has_service(DOMAIN, "deduct"):

        async def handle_deduct(call: ServiceCall):
            """Globalny serwis wywoływany z automatyzacji."""
            entity_id = call.data.get("entity_id")
            amount = float(call.data.get("amount", 0.0))

            state = hass.states.get(entity_id)
            if state:
                try:
                    current_weight = float(state.state)
                    new_weight = max(0.0, current_weight - amount)

                    # Aktualizacja stanu encji z zachowaniem jej atrybutów
                    hass.states.async_set(
                        entity_id, round(new_weight, 2), state.attributes
                    )
                    _LOGGER.info(
                        "SlimSpool: Odjęto %sg z %s. Pozostało: %s",
                        amount,
                        entity_id,
                        new_weight,
                    )
                except ValueError:
                    _LOGGER.error(
                        "SlimSpool: Błędny stan encji %s (oczekiwano liczby)", entity_id
                    )
            else:
                _LOGGER.warning("SlimSpool: Encja %s nie istnieje", entity_id)

        hass.services.async_register(DOMAIN, "deduct", handle_deduct)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Obsługa usunięcia szpuli przez interfejs użytkownika."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
