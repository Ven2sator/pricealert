import sys
import os
import re
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

# ==========================================
# KONFIGURATION
# ==========================================
# URL des Objekts / der Unterkunft
URL = "https://www.booking.com/hotel/de/beispiel.de.html"

# Dein Wunscheckpreis in Euro
TARGET_PRICE = 150.0

# Speicherort der Alarm-Historie
LOG_FILE = os.path.expanduser("~/preisalarme.log")

def extract_price(text):
    """
    Extrahiert eine Fließkommazahl aus Strings wie '€ 120,50' oder '120 €'.
    """
    if not text:
        return None
    # Punkte (Tausender) entfernen und Komma zu Punkt umwandeln
    cleaned = text.replace('.', '').replace(',', '.')
    match = re.search(r'(\d+(?:\.\d+)?)', cleaned)
    if match:
        return float(match.group(1))
    return None

def check_price():
    print(f"Starte Preisabfrage für: {URL}")
    
    with sync_playwright() as p:
        # Browser headless (im Hintergrund) starten
        browser = p.chromium.launch(headless=True)
        
        # User-Agent setzen, um als normaler Browser zu erscheinen
        context = browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="de-DE"
        )
        page = context.new_page()

        try:
            # Seite laden (max. 60s Timeout)
            page.goto(URL, wait_until="domcontentloaded", timeout=60000)
            time.sleep(3) # Kurze Pause zum Rendern von Preis-Komponenten

            # Versuchen, gängige Cookie-Banner zu schließen
            try:
                cookie_btn = page.query_selector("button#onetrust-accept-btn-handler, button[data-testid='gdpr-banner-accept']")
                if cookie_btn:
                    cookie_btn.click()
                    time.sleep(1)
            except Exception:
                pass

            # Verschiedene Preis-Selektoren (Booking / Airbnb) durchprobieren
            price_selectors = [
                "span[data-testid='price-and-discounted-price']", # Booking.com neu
                "span.prco-val-bignum",                          # Booking.com alt
                "div._1jo42nv",                                  # Airbnb
                "span._1y74zjx"                                  # Airbnb alt
            ]

            raw_price_text = None
            for selector in price_selectors:
                element = page.query_selector(selector)
                if element and element.inner_text().strip():
                    raw_price_text = element.inner_text().strip()
                    break

            if not raw_price_text:
                print("FEHLER: Keinen Preis auf der Seite gefunden. Evtl. Selektor anpassen.")
                browser.close()
                sys.exit(2)

            current_price = extract_price(raw_price_text)
            print(f"Gefundener Preis: {current_price} € (Text auf Seite: '{raw_price_text}')")

            browser.close()

            # Prüfen, ob der Zielpreis erreicht ist
            if current_price and current_price <= TARGET_PRICE:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                alarm_msg = f"[{timestamp}] ALARM: Zielpreis erreicht! Aktueller Preis: {current_price:.2f} € (Ziel: <= {TARGET_PRICE:.2f} €)"
                
                # 1. In Logdatei speichern
                with open(LOG_FILE, "a", encoding="utf-8") as f:
                    f.write(alarm_msg + "\n")

                # 2. Ausgeben und mit Status 0 (Erfolg) beenden
                print(alarm_msg)
                sys.exit(0)
            else:
                print(f"Kein Alarm: Aktueller Preis ({current_price} €) > Zielpreis ({TARGET_PRICE} €).")
                sys.exit(1)

        except Exception as e:
            print(f"FEHLER beim Scrapen: {e}")
            browser.close()
            sys.exit(2)

if __name__ == "__main__":
    check_price()
