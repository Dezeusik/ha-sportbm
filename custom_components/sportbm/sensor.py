from __future__ import annotations
from datetime import timedelta
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.util import dt as dt_util
from . import parser as P
from .const import DOMAIN
from .entity import ClubEntity, PlayerEntity


async def async_setup_entry(hass, entry, async_add):
    c = hass.data[DOMAIN][entry.entry_id]
    ents = [Unread(c, entry), LastMessage(c, entry), LastNotification(c, entry)]
    for pid in c.data["zawodnicy"]:
        ents += [cls(c, entry, pid) for cls in (NextTraining, WeekTrainings, Attendance, LastTraining, ToPay)]
    async_add(ents)


def _dt(s):
    return dt_util.parse_datetime(s) if s else None


def _upcoming(trainings):
    now = dt_util.now()
    return [t for t in trainings if t["koniec"] and _dt(t["koniec"]) and _dt(t["koniec"]) > now]


class NextTraining(PlayerEntity, SensorEntity):
    key, _attr_name, _attr_icon = "next_training", "Następny trening", "mdi:whistle"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    @property
    def native_value(self):
        u = _upcoming(self.p["treningi"])
        return _dt(u[0]["start"]) if u else None

    @property
    def extra_state_attributes(self):
        u = _upcoming(self.p["treningi"])
        if not u:
            return {}
        t = u[0]
        s = _dt(t["start"])
        return {"nazwa": t["nazwa"], "miejsce": t["miejsce"], "adres": t["adres"], "rodzaj": t["rodzaj"],
                "godziny": f"{dt_util.as_local(s):%H:%M}–{dt_util.as_local(_dt(t['koniec'])):%H:%M}", "zbiorka": t["zbiorka"]}


class WeekTrainings(PlayerEntity, SensorEntity):
    key, _attr_name, _attr_icon = "week_trainings", "Treningi w 7 dni", "mdi:calendar-week"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def _list(self):
        end = dt_util.now() + timedelta(days=7)
        return [t for t in _upcoming(self.p["treningi"]) if _dt(t["start"]) < end]

    @property
    def native_value(self):
        return len(self._list())

    @property
    def extra_state_attributes(self):
        return {"treningi": [{"kiedy": f"{dt_util.as_local(_dt(t['start'])):%a %d.%m %H:%M}", "nazwa": t["nazwa"], "miejsce": t["miejsce"]}
                             for t in self._list()]}


class Attendance(PlayerEntity, SensorEntity):
    key, _attr_name, _attr_icon = "attendance", "Frekwencja", "mdi:account-check"
    _attr_native_unit_of_measurement = "%"
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        return self.p["statystyki"].get("frequency")

    @property
    def extra_state_attributes(self):
        s = self.p["statystyki"]
        return {"obecny": s.get("present"), "nieobecny": s.get("absent"), "zgloszone_nieobecnosci": s.get("absence_reported"),
                "wszystkie": s.get("all")}


class LastTraining(PlayerEntity, SensorEntity):
    key, _attr_name, _attr_icon = "last_training", "Ostatni trening", "mdi:history"

    def _last(self):
        now = dt_util.now()
        past = [t for t in self.p["treningi"] if t["start"] and _dt(t["start"]) <= now]
        return past[-1] if past else None

    @property
    def native_value(self):
        t = self._last()
        return t["obecnosc"] if t else None

    @property
    def extra_state_attributes(self):
        t = self._last()
        return {"kiedy": t["start"], "nazwa": t["nazwa"], "spoznienie": t["spoznienie"], "powod": t["powod_nieobecnosci"]} if t else {}


class ToPay(PlayerEntity, SensorEntity):
    key, _attr_name, _attr_icon = "to_pay", "Do zapłaty", "mdi:cash-clock"
    _attr_native_unit_of_measurement = "zł"

    @property
    def native_value(self):
        return round(sum(x["kwota"] for x in P.unpaid(self.p["platnosci"])), 2)

    @property
    def extra_state_attributes(self):
        up = P.unpaid(self.p["platnosci"])
        paid = [x for x in self.p["platnosci"] if x["status"] == "paid"]
        return {"nieoplacone": up, "najblizszy_termin": up[0]["termin"] if up else None,
                "ostatnia_oplacona": paid[-1] if paid else None}


class Unread(ClubEntity, SensorEntity):
    key, _attr_name, _attr_icon = "unread", "Nieprzeczytane wiadomości", "mdi:email-alert"
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        return self.d.get("nieprzeczytane")


class LastMessage(ClubEntity, SensorEntity):
    key, _attr_name, _attr_icon = "last_message", "Ostatnia wiadomość", "mdi:message-text"

    @property
    def native_value(self):
        m = self.d.get("wiadomosci") or []
        return m[0]["tresc"][:255] if m else None

    @property
    def extra_state_attributes(self):
        m = self.d.get("wiadomosci") or []
        return {**(m[0] if m else {}), "nieprzeczytane": [x for x in m if not x["przeczytana"]][:5]}


class LastNotification(ClubEntity, SensorEntity):
    key, _attr_name, _attr_icon = "last_notification", "Ostatnie powiadomienie", "mdi:bell-ring"

    @property
    def native_value(self):
        n = self.d.get("powiadomienia") or []
        return (n[0]["tytul"] or n[0]["akcja_opis"])[:255] if n else None

    @property
    def extra_state_attributes(self):
        n = self.d.get("powiadomienia") or []
        return {**(n[0] if n else {}), "ostatnie": n[:5]}
