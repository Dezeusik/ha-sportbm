#!/usr/bin/env python3
"""Test logowania do SportBM bez Home Assistanta (biblioteka standardowa).
    curl -sL https://raw.githubusercontent.com/Dezeusik/ha-sportbm/main/tools/test_login.py | python3 - twoj@email
Hasło wpisujesz lokalnie; trafia tylko do app.sportbm.com."""
import getpass, http.cookiejar, json, sys, urllib.error, urllib.request
from datetime import date, timedelta

B = "https://app.sportbm.com/"
jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
H = {"Accept": "application/json, text/plain, */*", "Accept-Language": "pl,en", "Origin": B.rstrip("/"), "Referer": B}


def call(method, path, body=None):
    hdr = dict(H)
    csrf = next((c.value for c in jar if c.name == "csrftoken"), None)
    if body is not None:
        hdr["Content-Type"] = "application/json"
        if csrf:
            hdr["X-CSRFToken"] = csrf
    req = urllib.request.Request(B + path, method=method, headers=hdr, data=json.dumps(body).encode() if body is not None else None)
    try:
        with op.open(req, timeout=30) as r:
            raw = r.read()
            return r.status, (json.loads(raw) if raw[:1] in (b"{", b"[") else raw[:200])
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")[:300]


email = sys.argv[1] if len(sys.argv) > 1 else input("E-mail: ")
call("GET", "")
s, d = call("POST", "api/v2/auth/login/", {"email": email.strip(), "password": getpass.getpass("Hasło do SportBM: ")})
print("Logowanie:", s, "" if s < 400 else d)
if s >= 400:
    sys.exit(1)
s, players = call("GET", "api/player/players/?page_size=50")
print("Zawodnicy:", s, [p.get("first_name") for p in players.get("results", [])] if isinstance(players, dict) else players)
t = date.today()
s, ev = call("GET", f"api/player/event-attendances/?date_from={t}&date_to={t + timedelta(days=7)}&page_size=50")
print("Treningi w 7 dni:", s, ev.get("count") if isinstance(ev, dict) else ev)
print("OK – integracja powinna działać." if s == 200 else "Coś nie tak – wklej wynik Claude'owi.")
