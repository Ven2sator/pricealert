# Preisalarm für Regionen (Booking.com)

Überwacht eine ganze Region (statt einer einzelnen URL) auf Booking.com,
loggt jede Preisprüfung in SQLite und benachrichtigt dich, wenn der
günstigste Treffer deinen Zielpreis erreicht oder unterschreitet.

## 1. Installation

```bash
cd price_watcher
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

## 2. Konfiguration

```bash
cp config.example.json config.json
```

Passe `config.json` an: Region(en), Zeitraum, Personenzahl, Zielpreis und
Prüfintervall. Mehrere `watches` sind möglich (z.B. mehrere Städte parallel).

## 3. Starten

**Dauerhafter Hintergrund-Loop** (prüft alle X Minuten laut Config):
```bash
python3 price_alert.py
```

**Einmalige Prüfung** (z.B. für cron/systemd-Timer):
```bash
python3 price_alert.py --once
```

## 4. Automatisch per Cron laufen lassen

```bash
crontab -e
```
Zeile hinzufügen (Beispiel: alle 2 Stunden):
```
0 */2 * * * cd /pfad/zu/price_watcher && venv/bin/python3 price_alert.py --once >> ~/price_watcher.log 2>&1
```

Hinweis: Das Popup-Fenster (Tkinter) braucht eine grafische Sitzung
(`DISPLAY`-Variable). Auf einem Server ohne GUI kommt nur die
Log-/Datenbank-Eintragung an – die native Desktop-Notification greift
dann ebenfalls nicht.

## 5. Daten einsehen

```bash
sqlite3 ~/price_watcher.db "SELECT * FROM price_checks ORDER BY id DESC LIMIT 20;"
sqlite3 ~/price_watcher.db "SELECT * FROM alerts ORDER BY id DESC LIMIT 20;"
```

## Hinweise zur Robustheit

- Booking.com ändert sein HTML regelmäßig. Wenn `scraper.py` plötzlich
  "Keine Ergebnisse gefunden" meldet, müssen die CSS-Selektoren in
  `scraper.py` (Suche nach `data-testid`) angepasst werden.
- Die Anti-Blocking-Maßnahmen (realistischer User-Agent, Locale,
  Zeitzone, kein `navigator.webdriver`-Flag, kleine Zufalls-Pausen)
  reduzieren das Risiko einer Blockade, garantieren aber nichts.
- Bitte die Nutzungsbedingungen von Booking.com/Airbnb beachten – die
  Skripte sind für den persönlichen, nicht-kommerziellen Gebrauch gedacht.
- Airbnb ist deutlich aggressiver gegen automatisierte Zugriffe
  abgesichert; `scraper.py` enthält aktuell nur die Booking.com-Variante.
  Bei Bedarf kann nach demselben Muster ein `scrape_airbnb_region()`
  ergänzt werden.
