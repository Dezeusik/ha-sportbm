"""Uproszczenie odpowiedzi SportBM (bez zależności od HA). Celowo pomija dane wrażliwe (PESEL itp.)."""
from __future__ import annotations
import re
from html import unescape
from typing import Any

ATT = {"present": "obecny", "absent": "nieobecny", "unknown": "zaplanowany", "absence_reported": "nieobecność zgłoszona"}
ACTIONS = {"payment_occurrence_created": "nowa płatność", "payment_occurrence_paid": "płatność zaksięgowana",
           "message_notification": "nowa wiadomość", "event_occurrence_revoked": "trening odwołany",
           "event_occurrence_created": "nowy trening", "event_occurrence_changed": "zmiana treningu"}


def text(v: Any, n: int = 500) -> str:
    s = unescape(re.sub(r"<br\s*/?>|</p>", "\n", str(v or ""), flags=re.I))
    s = re.sub(r"<[^>]+>", "", s)
    s = "\n".join(" ".join(line.split()) for line in s.splitlines())
    return re.sub(r"\n{2,}", "\n", s).strip()[:n]


def person(u: dict | None) -> str:
    u = u or {}
    return f"{u.get('first_name', '')} {u.get('last_name', '')}".strip()


def players(items: list) -> list[dict]:
    return [{"id": str(p["id"]), "imie": p.get("first_name") or "", "nazwisko": p.get("last_name") or "",
             "klucz": person(p)} for p in items or []]


def events(items: list) -> list[dict]:
    out = []
    for a in items or []:
        eo = a.get("event_occurrence") or {}
        out.append({"id": str(a.get("id")), "kto": person(a.get("user")), "nazwa": text(eo.get("name"), 120),
                    "start": eo.get("date_from"), "koniec": eo.get("date_to"), "miejsce": text(eo.get("place"), 120),
                    "adres": text(eo.get("map_address"), 160), "zbiorka": eo.get("meet_up"),
                    "rodzaj": ((eo.get("event") or {}).get("type_display") or (eo.get("event") or {}).get("type")),
                    "obecnosc": ATT.get(a.get("type"), a.get("type")), "spoznienie": bool(a.get("was_late")),
                    "powod_nieobecnosci": text(a.get("absence_reason_display") or a.get("absence_other_text"), 120) or None})
    return sorted(out, key=lambda e: e["start"] or "")


def payments(items: list) -> list[dict]:
    out = []
    for p in items or []:
        try:
            amount = float(str(p.get("amount", "0")).replace(",", "."))
        except ValueError:
            amount = 0.0
        out.append({"id": str(p.get("id")), "kto": person(p.get("user")), "nazwa": text(p.get("name") or p.get("payment_name"), 120),
                    "kwota": round(amount, 2), "waluta": p.get("currency"), "termin": p.get("maturity_date"),
                    "status": p.get("state"), "status_opis": p.get("state_display"), "zaksiegowano": p.get("accounting_date")})
    return sorted(out, key=lambda x: x["termin"] or "")


def unpaid(pays: list[dict]) -> list[dict]:
    return [p for p in pays if p["status"] not in ("paid", "refunded", "cancelled", "canceled")]


def messages(items: list) -> list[dict]:
    return sorted([{"id": str(m.get("id")), "tresc": text(m.get("description"), 1000), "data": m.get("sending_date"),
                    "przeczytana": bool(m.get("is_read")), "klub": ((m.get("project") or {}).get("display_name")),
                    "zalacznikow": len(m.get("attachments") or [])} for m in items or []],
                  key=lambda m: m["data"] or "", reverse=True)


def notifications(items: list) -> list[dict]:
    return sorted([{"id": str(n.get("id")), "akcja": n.get("action"), "akcja_opis": ACTIONS.get(n.get("action"), n.get("action")),
                    "tytul": text(n.get("title_notification"), 120), "tresc": text(n.get("content") or n.get("short_content"), 600),
                    "data": n.get("created_at")} for n in items or []],
                  key=lambda n: n["data"] or "", reverse=True)
