from __future__ import annotations
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN


class ClubEntity(CoordinatorEntity):
    _attr_has_entity_name = True
    key = ""

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_{self.key}"
        self._attr_device_info = {"identifiers": {(DOMAIN, entry.entry_id)},
                                  "name": f"SportBM – {coordinator.data.get('klub') or 'klub'}", "manufacturer": "sportbm"}

    @property
    def d(self) -> dict:
        return self.coordinator.data or {}


class PlayerEntity(CoordinatorEntity):
    _attr_has_entity_name = True
    key = ""

    def __init__(self, coordinator, entry, pid: str) -> None:
        super().__init__(coordinator)
        self.pid = pid
        p = coordinator.data["zawodnicy"][pid]
        self._attr_unique_id = f"{entry.entry_id}_{pid}_{self.key}"
        self._attr_device_info = {"identifiers": {(DOMAIN, f"{entry.entry_id}_{pid}")},
                                  "name": f"SportBM – {p['imie']}", "manufacturer": "sportbm",
                                  "model": coordinator.data.get("klub") or "Zawodnik",
                                  "via_device": (DOMAIN, entry.entry_id)}

    @property
    def p(self) -> dict:
        return (self.coordinator.data or {}).get("zawodnicy", {}).get(self.pid, {})

    @property
    def available(self) -> bool:
        return super().available and bool(self.p)
