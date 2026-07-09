"""Definicja encji szpuli dla SlimSpool."""

import logging

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_COLOR,
    CONF_DENSITY,
    CONF_INITIAL_WEIGHT,
    CONF_MATERIAL,
    DOMAIN,
    UNIT_MM,
    UNIT_MM3,
)

_LOGGER = logging.getLogger(__name__)

COLOR_ICONS = {
    "Czarny": "mdi:circle-slice-8",
    "Biały": "mdi:circle-outline",
    "Szary": "mdi:circle",
    "Czerwony": "mdi:palette-swatch",
    "Niebieski": "mdi:water",
    "Zielony": "mdi:leaf",
    "Żółty": "mdi:star",
    "Pomarańczowy": "mdi:fruit-citrus",
    "Przezroczysty": "mdi:blur-linear",
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Dodanie encji szpuli."""
    config = entry.data
    async_add_entities(
        [
            SlimSpoolSpoolEntity(
                entry.unique_id,
                config.get("name"),
                config.get(CONF_MATERIAL),
                config.get(CONF_COLOR),
                config.get(CONF_INITIAL_WEIGHT),
                config.get(CONF_DENSITY, 1.24),
            )
        ],
        True,
    )


class SlimSpoolSpoolEntity(NumberEntity):
    """Obiekt szpuli filamentu z obsługą przeliczania gęstości."""

    def __init__(self, unique_id, name, material, color, initial_weight, density):
        self._attr_unique_id = unique_id
        self._attr_name = name
        self._material = material
        self._color = color
        self._density = float(density)
        self._state = float(initial_weight)
        self._location = "Na półce"

        self._attr_mode = NumberMode.BOX
        self._attr_native_min_value = 0.0
        self._attr_native_max_value = 2000.0
        self._attr_native_step = 0.1

    @property
    def native_value(self):
        return self._state

    @property
    def native_unit_of_measurement(self):
        return "g"

    @property
    def icon(self):
        return COLOR_ICONS.get(self._color, "mdi:printer-3d-nozzle")

    @property
    def extra_state_attributes(self):
        return {
            "material": self._material,
            "color": self._color,
            "density": self._density,
            "status_lokalizacji": self._location,
        }

    async def async_set_native_value(self, value: float) -> None:
        self._state = round(max(0.0, value), 2)
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(
            self.hass.bus.async_listen(
                "slimspool_relations_updated", self._update_location
            )
        )
        self.async_on_remove(
            self.hass.bus.async_listen(
                "slimspool_deduct_weight", self._handle_auto_deduct
            )
        )
        self._update_location(None)

    def _update_location(self, event: Event = None) -> None:
        current_location = "Na półce"
        devices = self.hass.data[DOMAIN]["devices"]

        for dev_id, dev_data in devices.items():
            sensor_id = dev_data["active_sensor"]
            state_obj = self.hass.states.get(sensor_id)

            if state_obj and state_obj.state.lower() == self._attr_name.lower():
                current_location = f"W urządzeniu: {dev_data['name']}"
                break

        if self._location != current_location:
            self._location = current_location
            self.async_write_ha_state()

    def _handle_auto_deduct(self, event: Event) -> None:
        """Automatyczne odejmowanie z przeliczaniem gęstości."""
        spool_name = event.data.get("spool_name")
        amount = event.data.get("amount", 0.0)
        unit = event.data.get("unit")

        if spool_name and spool_name.lower() == self._attr_name.lower():
            weight_to_deduct = amount

            # PRZELICZENIA MATEMATYCZNE NA PODSTAWIE JEDNOSTEK
            if unit == UNIT_MM3:
                # mm³ na gramy: (objętość * gęstość) / 1000
                weight_to_deduct = (amount * self._density) / 1000.0
            elif unit == UNIT_MM:
                # mm na gramy dla 1.75mm: (długość * 2.40528 * gęstość) / 1000
                weight_to_deduct = (amount * 2.405281 * self._density) / 1000.0

            self._state = round(max(0.0, self._state - weight_to_deduct), 2)
            _LOGGER.info(
                "SlimSpool: Konwersja z %s. Odjęto %sg z %s",
                unit,
                round(weight_to_deduct, 4),
                self._attr_name,
            )
            self.async_write_ha_state()
