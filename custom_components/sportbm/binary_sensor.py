from __future__ import annotations
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.util import dt as dt_util
from .const import DOMAIN
from .entity import PlayerEntity


async def async_setup_entry(hass, entry, async_add):
    c = hass.data[DOMAIN][entry.entry_id]
    async_add([TrainingToday(c, entry, pid) for pid in c.data["zawodnicy"]])


class TrainingToday(PlayerEntity, BinarySensorEntity):
    key, _attr_name, _attr_icon = "training_today", "Trening dziś", "mdi:soccer"

    @property
    def is_on(self):
        today = dt_util.now().date()
        return any(t["start"] and dt_util.as_local(dt_util.parse_datetime(t["start"])).date() == today
                   and t["obecnosc"] != "nieobecność zgłoszona" for t in self.p["treningi"])
