from __future__ import annotations
import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from .api import SportBMAuthError, SportBMClient
from .const import CONF_EMAIL, CONF_PASSWORD, CONF_SCAN_MINUTES, DEFAULT_SCAN_MINUTES, DOMAIN, MIN_SCAN_MINUTES

_LOGGER = logging.getLogger(__name__)
_INTERVAL = vol.All(vol.Coerce(int), vol.Range(min=MIN_SCAN_MINUTES, max=1440))


class SportBMFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return SportBMOptionsFlow()

    async def _check(self, data) -> tuple[list, str | None, str]:
        c = SportBMClient(async_create_clientsession(self.hass), data[CONF_EMAIL], data[CONF_PASSWORD])
        try:
            await c.login()
            roles = await c.get_all("api/player/players/")
        except SportBMAuthError as e:
            return [], "auth", str(e)
        except Exception as e:  # noqa: BLE001
            _LOGGER.exception("SportBM: test logowania nie powiódł się")
            return [], "connect", f"{type(e).__name__}: {e}"[:300]
        return roles, None, ""

    async def async_step_user(self, user_input=None):
        errors, details = {}, ""
        if user_input:
            roles, err, details = await self._check(user_input)
            if err:
                errors["base"] = err
            else:
                await self.async_set_unique_id(user_input[CONF_EMAIL].strip().lower())
                self._abort_if_unique_id_configured()
                kids = ", ".join(r.get("first_name") or "?" for r in roles)
                return self.async_create_entry(title=f"SportBM – {kids}", data=user_input)
        schema = vol.Schema({vol.Required(CONF_EMAIL): str, vol.Required(CONF_PASSWORD): str,
                             vol.Optional(CONF_SCAN_MINUTES, default=DEFAULT_SCAN_MINUTES): _INTERVAL})
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors,
                                    description_placeholders={"details": details})

    async def async_step_reauth(self, entry_data):
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None):
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        errors, details = {}, ""
        if user_input:
            _r, err, details = await self._check({**entry.data, CONF_PASSWORD: user_input[CONF_PASSWORD]})
            if err:
                errors["base"] = err
            else:
                self.hass.config_entries.async_update_entry(entry, data={**entry.data, CONF_PASSWORD: user_input[CONF_PASSWORD]})
                await self.hass.config_entries.async_reload(entry.entry_id)
                return self.async_abort(reason="reauth_successful")
        return self.async_show_form(step_id="reauth_confirm", data_schema=vol.Schema({vol.Required(CONF_PASSWORD): str}),
                                    errors=errors, description_placeholders={"details": details})


class SportBMOptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        cur = self.config_entry.options.get(CONF_SCAN_MINUTES, self.config_entry.data.get(CONF_SCAN_MINUTES, DEFAULT_SCAN_MINUTES))
        return self.async_show_form(step_id="init", data_schema=vol.Schema({vol.Required(CONF_SCAN_MINUTES, default=int(cur)): _INTERVAL}))
