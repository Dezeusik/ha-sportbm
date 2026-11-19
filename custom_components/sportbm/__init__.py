from __future__ import annotations
from datetime import timedelta
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from .api import SportBMClient
from .const import CONF_EMAIL, CONF_PASSWORD, CONF_SCAN_MINUTES, DEFAULT_SCAN_MINUTES, DOMAIN
from .coordinator import SportBMCoordinator

PLATFORMS = ["sensor", "binary_sensor", "calendar"]


def _minutes(entry: ConfigEntry) -> int:
    return int(entry.options.get(CONF_SCAN_MINUTES, entry.data.get(CONF_SCAN_MINUTES, DEFAULT_SCAN_MINUTES)))


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    client = SportBMClient(async_create_clientsession(hass), entry.data[CONF_EMAIL], entry.data[CONF_PASSWORD])
    coord = SportBMCoordinator(hass, client, entry.entry_id, _minutes(entry))
    await coord.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coord
    entry.async_on_unload(entry.add_update_listener(_options_updated))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return ok


async def _options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    coord = hass.data[DOMAIN][entry.entry_id]
    coord.update_interval = timedelta(minutes=_minutes(entry))
    await coord.async_request_refresh()
