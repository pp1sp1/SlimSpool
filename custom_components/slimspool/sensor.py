"""Definicja sensora wagi filamentu dla SlimSpool."""

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_COLOR, CONF_INITIAL_WEIGHT, CONF_MATERIAL


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Tworzenie encji sensora na podstawie danych z przepływu konfiguracji."""
    config = entry.data
    name = config.get("name")
    material = config.get(CONF_MATERIAL)
    color = config.get(CONF_COLOR)
    initial_weight = config.get(CONF_INITIAL_WEIGHT)
    unique_id = entry.unique_id

    async_add_entities(
        [SlimSpoolSensor(unique_id, name, material, color, initial_weight)], True
    )


class SlimSpoolSensor(SensorEntity):
    """Reprezentacja szpuli filamentu jako sensora Home Assistant."""

    def __init__(self, unique_id, name, material, color, initial_weight):
        """Inicjalizacja sensora."""
        self._attr_unique_id = unique_id
        self._attr_name = name
        self._material = material
        self._color = color
        self._state = initial_weight

    @property
    def state(self):
        """Zwraca aktualną wagę filamentu."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Zwraca jednostkę miary (gramy)."""
        return "g"

    @property
    def icon(self):
        """Ikona sensora w HA."""
        return "mdi:printer-3d-nozzle"

    @property
    def extra_state_attributes(self):
        """Zwraca parametry szpuli jako atrybuty stanu."""
        return {"material": self._material, "color": self._color}
