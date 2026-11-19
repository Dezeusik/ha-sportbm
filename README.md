# SportBM → Home Assistant (nieoficjalna integracja)

Integracja dla rodziców korzystających z **SportBM** (app.sportbm.com): treningi, obecności, płatności,
wiadomości i powiadomienia klubu. Korzysta z tego samego API co aplikacja webowa i loguje się e-mailem i hasłem.
Każdy zawodnik z konta ma własne urządzenie w HA.

> Projekt prywatny, niezwiązany z sportbm sp. z o.o. Używaj tylko z własnym kontem.
> Integracja nie pobiera i nie zapisuje numerów PESEL, chociaż API je zwraca.

## Instalacja
HACS → ⋮ → *Custom repositories* → `https://github.com/Dezeusik/ha-sportbm` (Integration) → pobierz „SportBM” →
Ustawienia → Urządzenia i usługi → Dodaj integrację → **SportBM**. Domyślnie dane odświeżają się co 15 min, minimum to 10.

Test bez HA: `curl -sL https://raw.githubusercontent.com/Dezeusik/ha-sportbm/main/tools/test_login.py | python3 - twoj@email`

## Encje
**Każdy zawodnik:** Następny trening (czas; nazwa, miejsce, godziny), Treningi w 7 dni, Frekwencja %,
Ostatni trening (obecny/nieobecny), Do zapłaty (zł; lista nieopłaconych), czujnik binarny Trening dziś.

**Klub:** Nieprzeczytane wiadomości, Ostatnia wiadomość, Ostatnie powiadomienie oraz kalendarz **Treningi**
(wszyscy zawodnicy, 3 tygodnie do przodu).

## Zdarzenia
- `sportbm_powiadomienie` – każde nowe powiadomienie klubu: `akcja` (np. `event_occurrence_revoked`), `akcja_opis`
  („trening odwołany”, „nowa płatność”, „płatność zaksięgowana”, „nowa wiadomość”), `tytul`, `tresc`, `data`
- `sportbm_wiadomosc` – nowa, nieprzeczytana wiadomość: `tresc`, `data`, `klub`, `zalacznikow`

Przy pierwszym uruchomieniu zdarzenia nie są wysyłane.
