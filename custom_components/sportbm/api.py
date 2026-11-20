"""Klient API SportBM (to samo API co app.sportbm.com, sesja Django w ciasteczkach)."""
from __future__ import annotations
import logging
from typing import Any
import aiohttp
from yarl import URL
from .const import BASE_URL

_LOGGER = logging.getLogger(__name__)
HEADERS = {"Accept": "application/json, text/plain, */*", "Accept-Language": "pl,en",
           "Origin": "https://app.sportbm.com", "Referer": "https://app.sportbm.com/",
           "User-Agent": "Mozilla/5.0 (compatible; ha-sportbm/0.1; +https://github.com/Dezeusik/ha-sportbm)"}


class SportBMAuthError(Exception):
    pass


class SportBMError(Exception):
    pass


class SportBMClient:
    def __init__(self, session: aiohttp.ClientSession, email: str, password: str) -> None:
        self._s, self._email, self._password = session, email.strip(), password
        self._logged = False

    def _csrf(self) -> str | None:
        c = self._s.cookie_jar.filter_cookies(URL(BASE_URL)).get("csrftoken")
        return c.value if c else None

    async def login(self) -> dict:
        async with self._s.get(BASE_URL, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=30)) as r:
            await r.read()
        hdr = {**HEADERS, "Content-Type": "application/json"}
        if self._csrf():
            hdr["X-CSRFToken"] = self._csrf()
        async with self._s.post(BASE_URL + "api/v2/auth/login/", json={"username": self._email, "password": self._password},
                                headers=hdr, timeout=aiohttp.ClientTimeout(total=30)) as r:
            text = await r.text()
            if r.status in (400, 401, 403):
                raise SportBMAuthError(f"HTTP {r.status}: {text[:200]}")
            if r.status >= 400:
                raise SportBMError(f"login HTTP {r.status}")
        me = await self.get("api/common/me/", _retry=False)
        self._logged = True
        return me if isinstance(me, dict) else {}

    async def get(self, path: str, params: dict | None = None, _retry: bool = True) -> Any:
        for attempt in (0, 1):
            if not self._logged and _retry:
                await self.login()
            async with self._s.get(BASE_URL + path, params=params, headers=HEADERS,
                                   timeout=aiohttp.ClientTimeout(total=30)) as r:
                if r.status in (401, 403) and attempt == 0 and _retry:
                    self._logged = False
                    continue
                if r.status in (401, 403):
                    raise SportBMAuthError(f"{path}: HTTP {r.status}")
                if r.status >= 400:
                    raise SportBMError(f"{path}: HTTP {r.status}")
                return await r.json(content_type=None)
        raise SportBMError(path)

    async def get_all(self, path: str, params: dict | None = None, limit: int = 300) -> list:
        """Paginacja DRF (count/next/results)."""
        out, page = [], 1
        while len(out) < limit:
            data = await self.get(path, {**(params or {}), "page": page, "page_size": 100})
            if isinstance(data, list):
                return data
            out += data.get("results") or []
            if not data.get("next"):
                break
            page += 1
        return out
