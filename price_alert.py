#!/usr/bin/env python3
"""
price_alert.py – Automatisierter Preisalarm für ganze Regionen.

Nutzung:
    python3 price_alert.py                # läuft dauerhaft im Loop
    python3 price_alert.py --once          # prüft nur einmal (z.B. für cron)
    python3 price_alert.py --config x.json # eigene Konfiguration verwenden
"""

import argparse
import json
import os
import time
from datetime import datetime

from db import init_db, log_price_check, log_alert
from notifier import send_desktop_notification, show_alert_window
from scraper import scrape_booking_region

DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")


def load_config(path):
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Konfigurationsdatei nicht gefunden: {path}\n"
            f"Kopiere config.example.json nach config.json und passe sie an."
        )
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_watch(watch, db_path, open_windows):
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] Prüfe '{watch['name']}' ({watch['region']}) ...")

    listings = scrape_booking_region(
        region=watch["region"],
        checkin=watch["checkin"],
        checkout=watch["checkout"],
        adults=watch.get("adults", 2),
        max_results=watch.get("max_results", 5),
    )

    if not listings:
        print("  Keine Ergebnisse gefunden (Selektoren evtl. veraltet oder Anfrage blockiert).")
        return

    for item in listings:
        log_price_check(
            watch_name=watch["name"],
            region=watch["region"],
            source="booking",
            listing_name=item["name"],
            price=item["price"],
            url=item["url"],
            db_path=db_path,
        )

    cheapest = min(listings, key=lambda x: x["price"])
    print(f"  Günstigstes Angebot: {cheapest['name']} – {cheapest['price']:.2f} €")

    target = watch["target_price"]
    if cheapest["price"] <= target:
        msg = (
            f"{cheapest['name']}\n{cheapest['price']:.2f} € "
            f"(Ziel: <= {target:.2f} €)\nRegion: {watch['region']}"
        )
        log_alert(
            watch_name=watch["name"],
            region=watch["region"],
            listing_name=cheapest["name"],
            price=cheapest["price"],
            target_price=target,
            url=cheapest["url"],
            db_path=db_path,
        )
        send_desktop_notification(f"Preisalarm: {watch['name']}", msg)
        open_windows.append(show_alert_window(f"Preisalarm: {watch['name']}", msg))
    else:
        print(f"  Kein Alarm ({cheapest['price']:.2f} € > {target:.2f} €).")


def main():
    parser = argparse.ArgumentParser(description="Automatisierter Preisalarm für Booking.com-Regionen")
    parser.add_argument("--config", default=DEFAULT_CONFIG_PATH, help="Pfad zur config.json")
    parser.add_argument("--once", action="store_true", help="Nur einmal prüfen statt Endlos-Loop")
    args = parser.parse_args()

    config = load_config(args.config)
    db_path = os.path.expanduser(config.get("database", "~/price_watcher.db"))
    init_db(db_path)

    interval_seconds = config.get("check_interval_minutes", 60) * 60
    open_windows = []

    while True:
        for watch in config.get("watches", []):
            try:
                run_watch(watch, db_path, open_windows)
            except Exception as e:
                print(f"  FEHLER bei Watch '{watch.get('name')}': {e}")

        if args.once:
            # Falls ein Alarm-Fenster geöffnet wurde, warten wir, bis der
            # Nutzer es schließt, statt den Prozess sofort zu beenden.
            for t in open_windows:
                t.join()
            break

        print(f"Warte {interval_seconds // 60} Minuten bis zur nächsten Prüfung ...\n")
        time.sleep(interval_seconds)


if __name__ == "__main__":
    main()
