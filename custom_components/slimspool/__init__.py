import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Konfiguracja wpisu z GUI."""
    hass.data.setdefault(DOMAIN, {})

    # Przekazujemy załadowanie encji do pliku sensor.py
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Rejestrujemy usługę deduct globalnie (tylko raz)
    if not hass.services.has_service(DOMAIN, "deduct"):

        async def handle_deduct(call: ServiceCall):
            """Usługa wywoływana np. z automatyzacji Klippera."""
            entity_id = call.data.get("entity_id")
            amount = float(call.data.get("amount", 0.0))

            # Szukamy encji w rejestrze urządzeń i zmieniamy jej stan
            state = hass.states.get(entity_id)
            if state:
                try:
                    current_weight = float(state.state)
                    new_weight = max(0.0, current_weight - amount)

                    # Nadpisujemy stan encji zachowując jej dotychczasowe atrybuty (kolor, materiał)
                    hass.states.async_set(
                        entity_id, round(new_weight, 2), state.attributes
                    )
                    _LOGGER.info(
                        "Odjęto %sg z %s. Zostało: %s", amount, entity_id, new_weight
                    )
                except ValueError:
                    _LOGGER.error("Błędny stan obecny encji %s", entity_id)
            else:
                _LOGGER.warning("Encja %s nie istnieje", entity_id)

        hass.services.async_register(DOMAIN, "deduct", handle_deduct)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Obsługa usunięcia szpuli z poziomu GUI."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
