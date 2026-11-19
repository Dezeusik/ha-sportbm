from __future__ import annotations
from datetime import timedelta
import logging
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util
from . import parser as P
from .api import SportBMAuthError, SportBMClient
from .const import DAYS_AHEAD, DOMAIN, EVENT_MESSAGE, EVENT_NOTIFICATION

_LOGGER = logging.getLogger(__name__)


class SportBMCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, client: SportBMClient, entry_id: str, minutes: int) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=timedelta(minutes=minutes))
        self.client = client
        self._store = Store(hass, 1, f"{DOMAIN}_{entry_id}")
        self._seen: dict | None = None

    async def _async_update_data(self):
        if self._seen is None:
            self._seen = await self._store.async_load() or {}
        c = self.client
        today = dt_util.now().date()
        try:
            players = P.players(await c.get_all("api/player/players/"))
            clubs = await c.get("api/player/projects/all/")
            evs = P.events(await c.get_all("api/player/event-attendances/", {
                "date_from": (today - timedelta(days=7)).isoformat(), "date_to": (today + timedelta(days=DAYS_AHEAD)).isoformat()}))
            pays = P.payments(await c.get_all("api/player/payment-occurrences/"))
            msgs = P.messages((await c.get("api/common/messages/", {"page_size": 20})).get("results"))
            unread = (await c.get("api/common/messages/unread/")).get("count")
            nots = P.notifications((await c.get("api/common/notifications/", {"page_size": 20})).get("results"))
            stats = {}
            for p in players:
                try:
                    stats[p["id"]] = await c.get(f"api/player/players/{p['id']}/attendances/stats/")
                except Exception:  # noqa: BLE001
                    stats[p["id"]] = {}
        except SportBMAuthError as e:
            raise ConfigEntryAuthFailed(str(e)) from e
        except Exception as e:  # noqa: BLE001
            raise UpdateFailed(str(e)) from e
        data = {"klub": (clubs[0].get("display_name") if isinstance(clubs, list) and clubs else None),
                "zawodnicy": {}, "treningi": evs, "platnosci": pays, "wiadomosci": msgs,
                "nieprzeczytane": unread, "powiadomienia": nots}
        for p in players:
            data["zawodnicy"][p["id"]] = {**p, "statystyki": stats.get(p["id"]) or {},
                                          "treningi": [e for e in evs if e["kto"] == p["klucz"]],
                                          "platnosci": [x for x in pays if x["kto"] == p["klucz"]]}
        self._fire(data)
        await self._store.async_save(self._seen)
        return data

    def _fire(self, data: dict) -> None:
        first = "init" not in self._seen
        for key, items, ev in (("nots", data["powiadomienia"], EVENT_NOTIFICATION), ("msgs", data["wiadomosci"], EVENT_MESSAGE)):
            known = set(self._seen.get(key, []))
            if not first:
                for it in reversed(items):
                    if it["id"] not in known and not (ev == EVENT_MESSAGE and it["przeczytana"]):
                        self.hass.bus.async_fire(ev, {**it, "klub": data["klub"]})
            self._seen[key] = sorted(known | {it["id"] for it in items})[-500:]
        self._seen["init"] = True
