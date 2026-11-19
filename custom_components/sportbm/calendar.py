from __future__ import annotations
from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.util import dt as dt_util
from .const import DOMAIN
from .entity import ClubEntity


async def async_setup_entry(hass, entry, async_add):
    async_add([Trainings(hass.data[DOMAIN][entry.entry_id], entry)])


class Trainings(ClubEntity, CalendarEntity):
    key, _attr_name, _attr_icon = "calendar", "Treningi", "mdi:calendar-star"

    def _events(self):
        out = []
        for t in self.d.get("treningi") or []:
            s, e = dt_util.parse_datetime(t["start"] or ""), dt_util.parse_datetime(t["koniec"] or "")
            if not s or not e:
                continue
            first = t["kto"].split(" ")[0]
            out.append(CalendarEvent(start=s, end=e, summary=f"{first}: {t['nazwa']}", location=t["miejsce"] or t["adres"] or None,
                                     description=f"Obecność: {t['obecnosc']}", uid=f"sportbm-{t['id']}"))
        return out

    @property
    def event(self):
        now = dt_util.now()
        up = [e for e in self._events() if e.end > now]
        return min(up, key=lambda e: e.start) if up else None

    async def async_get_events(self, hass, start_date, end_date):
        return [e for e in self._events() if e.start < end_date and e.end > start_date]
