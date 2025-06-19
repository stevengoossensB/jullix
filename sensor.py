"""Platform for Jullix sensors."""
import logging
import json
import os
from datetime import timedelta, datetime, timezone

import async_timeout
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, CoordinatorEntity
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN, DEFAULT_SCAN_INTERVAL

# map each category to an mdi: icon
ICONS: dict[str, str] = {
    "meter": "mdi:flash",
    "solar": "mdi:solar-power",
    "battery": "mdi:battery",
    "charger": "mdi:ev-station",
    "plug": "mdi:power-plug",
}

_LOGGER = logging.getLogger(__name__)
# Load sensor_config from the same folder as this file
_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "sensor_config.json")
try:
    with open(_CONFIG_PATH) as f:
        SENSOR_CONFIG = json.load(f)
except FileNotFoundError:
    _LOGGER.error("sensor_config.json not found at %s", _CONFIG_PATH)
    SENSOR_CONFIG = {}

def _flatten(obj, parent_key: str = "", out: dict = None) -> dict:
    out = {} if out is None else out
    if isinstance(obj, dict):
        for k, v in obj.items():
            new_key = f"{parent_key}_{k}" if parent_key else k
            _flatten(v, new_key, out)
    else:
        out[parent_key] = obj
    return out

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
):
    """Set up Jullix sensors from a config entry."""
    session = async_get_clientsession(hass)
    host = hass.data[DOMAIN][entry.entry_id]["host"]

    async def fetch_json(endpoint: str):
        try:
            async with async_timeout.timeout(10):
                resp = await session.get(f"{host}{endpoint}")
                return await resp.json()
        except Exception as err:
            _LOGGER.error("Error fetching %s: %s", endpoint, err)
            return None

    async def _update():
        return {
            key: await fetch_json(f"/api/ems/{key}")
            for key in ["meter", "solar", "battery", "charger", "plug"]
        }

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="jullix",
        update_method=_update,
        update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
    )
    await coordinator.async_config_entry_first_refresh()

    entities = []
    for category, payload in coordinator.data.items():
        if not payload:
            continue
        samples = payload if isinstance(payload, list) else [payload]
        for sample in samples:
            device_id = sample.get("id") or sample.get("meter") or category
            name_base = sample.get("device", f"Jullix {category.title()}")
            flat = _flatten(sample)
            for key, val in flat.items():
#                if isinstance(val, (int, float)):
                  entities.append(
                      JullixSensor(coordinator, category, key, device_id, name_base)
                  )

    async_add_entities(entities)

class JullixSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, category, key, device_id, name_base):
        super().__init__(coordinator)
        self._attr_icon = ICONS.get(category)
        self._category = category
        self._key = key
        self._device_id = device_id
        self._name_base = name_base
        self._attr_name = f"{name_base} {key.replace('_',' ').title()}"
        self._attr_unique_id = f"jullix_{category}_{device_id}_{key}"
        try:
            self._attr_native_unit_of_measurement = SENSOR_CONFIG[category][key]["unit_of_measurement"]
        except KeyError:
            self._attr_native_unit_of_measurement = None  # set via config if needed

    @property
    def device_info(self) -> DeviceInfo:
        """Group sensors by physical device (meter, battery, etc)."""
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self._category}_{self._device_id}")},
            name=self._name_base,
            manufacturer="Jullix",
            model=self._category.title(),
        )

    @property
    def native_value(self):
        data = self.coordinator.data.get(self._category)
        if not data:
            return None
        if isinstance(data, list):
            # find the sample matching this sensor's device_id
            sample = next(
                (
                    d
                    for d in data
                    if (d.get("id") or d.get("meter") or self._category)
                    == self._device_id
                ),
                data[0],  # fallback to first sample if id not found
            )
        else:
            sample = data
        flat = _flatten(sample)
        val = flat.get(self._key)
        # Convert Jullix meter timestamps (e.g. 250518214500) to ISO8601
        if self._category == "meter" and self._key in ("time", "captar_month_max_time") and val:
            try:
                dt = datetime.strptime(str(val), "%y%m%d%H%M%S")
                return dt.replace(tzinfo=timezone.utc).isoformat()
            except ValueError:
                _LOGGER.error("Unable to parse timestamp %s for sensor %s", val, self._key)
        if isinstance(val, (int, float)):
            return round(val, 2)
        return val

    @property
    def icon(self) -> str | None:
        """Return mdi: icon based on category."""
        return ICONS.get(self._category)

