"""Definicja encji szpuli dla SlimSpool."""

import logging

from homeassistant.components.number import RestoreNumber, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
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


class SlimSpoolSpoolEntity(RestoreNumber):
    """Obiekt szpuli filamentu zachowujący stan po restarcie."""

    def __init__(self, unique_id, name, material, color, initial_weight, density):
        """Inicjalizacja encji."""
        self._attr_unique_id = unique_id
        self._attr_name = name
        self._material = material
        self._color = color
        self._density = float(density)

        # Wartość domyślna / ratunkowa (jeśli brak wpisu w bazie danych)
        self._state = float(initial_weight)
        self._location = "Na półce"

        self._attr_mode = NumberMode.BOX
        self._attr_native_min_value = 0.0
        self._attr_native_max_value = 5000.0
        self._attr_native_step = 0.1

    @property
    def native_value(self):
        """Zwraca aktualną wagę."""
        return self._state

    @property
    def native_unit_of_measurement(self):
        """Jednostka miary."""
        return "g"

    @property
    def icon(self):
        """Czytelna ikona szpuli 3D."""
        return "mdi:circle-slice-8"

    def _get_icon_color(self) -> str:
        """Zwraca kolor ikony na podstawie koloru filamentu."""
        if not self._color:
            return "grey"

        color = str(self._color).strip().lower()

        color_map = {
            # Polski
            "niebieski": "blue",
            "błękitny": "blue",
            "czerwony": "red",
            "zielony": "green",
            "żółty": "yellow",
            "pomarańczowy": "orange",
            "fioletowy": "purple",
            "różowy": "pink",
            "biały": "white",
            "czarny": "black",
            "szary": "grey",
            "szare": "grey",
            "srebrny": "silver",
            "złoty": "gold",
            # Angielski
            "blue": "blue",
            "red": "red",
            "green": "green",
            "yellow": "yellow",
            "orange": "orange",
            "purple": "purple",
            "pink": "pink",
            "white": "white",
            "black": "black",
            "grey": "grey",
            "gray": "grey",
            "silver": "silver",
            "gold": "gold",
        }

        return color_map.get(color, "grey")

    @property
    def extra_state_attributes(self):
        """Zwraca atrybuty encji do karty Tile."""
        return {
            "material": self._material,
            "kolor_filamentu": self._color,
            "gęstość": self._density,
            "status_lokalizacji": self._location,
            "icon_color": self._get_icon_color(),
        }

    async def async_set_native_value(self, value: float) -> None:
        """Obsługa ręcznej zmiany stanu za pomocą pola tekstowego/suwaka."""
        self._state = round(max(0.0, value), 2)
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Wywoływane przy rejestracji encji - przywracanie stanu."""
        await super().async_added_to_hass()

        # Próba odzyskania stanu z bazy danych
        last_number_data = await self.async_get_last_number_data()
        if last_number_data and last_number_data.native_value is not None:
            self._state = round(float(last_number_data.native_value), 2)
            _LOGGER.info("Przywrócono wagę szpuli %s z bazy: %s g", self._attr_name, self._state)
        else:
            last_state = await self.async_get_last_state()
            if last_state and last_state.state not in ("unknown", "unavailable"):
                try:
                    self._state = round(float(last_state.state), 2)
                except ValueError:
                    pass

        # Subskrypcje zdarzeń systemowych
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

        # Pierwsze wymuszenie odczytu pozycji
        self._update_location(None)

    @callback
    def _update_location(self, event: Event = None) -> None:
        """Dynamicznie wylicza pozycję (W bezpiecznej pętli callback)."""
        current_location = "Na półce"

        if DOMAIN in self.hass.data and "devices" in self.hass.data[DOMAIN]:
            devices = self.hass.data[DOMAIN]["devices"]

            for dev_id, dev_data in devices.items():
                sensor_id = dev_data.get("active_sensor")
                if not sensor_id or sensor_id == "Brak / Tylko lokalizacja":
                    continue

                state_obj = self.hass.states.get(sensor_id)
                if state_obj and state_obj.state.lower() == self._attr_name.lower():
                    current_location = f"W urządzeniu: {dev_data['name']}"
                    break

        if self._location != current_location:
            self._location = current_location
            self.async_write_ha_state()

    @callback
    def _handle_auto_deduct(self, event: Event) -> None:
        """Odejmowanie wartości (W bezpiecznej pętli callback)."""
        spool_name = event.data.get("spool_name")
        amount = event.data.get("amount", 0.0)
        unit = event.data.get("unit")

        if spool_name and spool_name.lower() == self._attr_name.lower():
            weight_to_deduct = amount

            if unit == UNIT_MM3:
                weight_to_deduct = (amount * self._density) / 1000.0
            elif unit == UNIT_MM:
                # Wzór dla dyszy/filamentu 1.75mm uwzględniający wybraną gęstość
                weight_to_deduct = (amount * 2.405281 * self._density) / 1000.0

            self._state = round(max(0.0, self._state - weight_to_deduct), 2)
            self.async_write_ha_state()
