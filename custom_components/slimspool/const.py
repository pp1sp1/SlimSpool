"""Stałe dla integracji SlimSpool."""

DOMAIN = "slimspool"

ENTRY_TYPE = "entry_type"
TYPE_SPOOL = "spool"
TYPE_DEVICE = "device"

# Pola dla Szpuli
CONF_COLOR = "color"
CONF_MATERIAL = "material"
CONF_INITIAL_WEIGHT = "initial_weight"
CONF_DENSITY = "density"  # <-- NOWOŚĆ

# Pola dla Urządzenia
CONF_DEVICE_TYPE = "device_type"
CONF_ACTIVE_SPOOL_SENSOR = "active_spool_sensor"
CONF_CONSUMPTION_SENSOR = "consumption_sensor"
CONF_CONSUMPTION_UNIT = "consumption_unit"  # <-- NOWOŚĆ

# Jednostki raportowania przez drukarkę
UNIT_GRAMS = "g (Waga)"
UNIT_MM3 = "mm³ (Objętość / Volumetric)"
UNIT_MM = "mm (Długość filamentu 1.75mm)"

CONSUMPTION_UNITS = [UNIT_GRAMS, UNIT_MM3, UNIT_MM]

AVAILABLE_COLORS = [
    "Czarny",
    "Biały",
    "Szary",
    "Czerwony",
    "Niebieski",
    "Zielony",
    "Żółty",
    "Pomarańczowy",
    "Przezroczysty",
]
