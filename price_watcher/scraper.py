"""
scraper.py – Simuliert einen echten Browser mit Playwright, um eine ganze
Region auf Booking.com nach Angeboten zu durchsuchen, statt nur eine
einzelne URL zu prüfen.

Anti-Blocking-Maßnahmen (kein Umgehen von Logins/Bezahlschranken, nur
alltägliche Tarnung eines Headless-Browsers):
- realistischer User-Agent (zufällig aus einer kleinen Liste)
- de-DE Locale, passende Zeitzone und Accept-Language-Header
- Entfernen des "navigator.webdriver"-Flags
- kleine, zufällige Wartezeiten statt sofortiger Anfragen
- Cookie-Banner werden automatisch weggeklickt

Hinweis: Booking.com/Airbnb ändern ihr HTML regelmäßig, daher können die
CSS-Selektoren nach einiger Zeit angepasst werden müssen. Bitte zusätzlich
die Nutzungsbedingungen der jeweiligen Plattform beachten.
"""

import random
import re
import time
from urllib.parse import quote_plus

from playwright.sync_api import sync_playwright

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]

STEALTH_INIT_SCRIPT = """
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
window.chrome = { runtime: {} };
Object.defineProperty(navigator, 'languages', { get: () => ['de-DE', 'de'] });
Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
"""


def _new_context(browser):
    context = browser.new_context(
        user_agent=random.choice(USER_AGENTS),
        locale="de-DE",
        viewport={"width": 1366, "height": 850},
        timezone_id="Europe/Berlin",
        extra_http_headers={"Accept-Language": "de-DE,de;q=0.9,en;q=0.8"},
    )
    context.add_init_script(STEALTH_INIT_SCRIPT)
    return context


def _accept_cookies(page):
    selectors = [
        "button#onetrust-accept-btn-handler",
        "button[data-testid='gdpr-banner-accept']",
        "button[aria-label='Accept']",
    ]
    for sel in selectors:
        try:
            el = page.query_selector(sel)
            if el:
                el.click()
                time.sleep(0.5)
                return
        except Exception:
            pass


def _human_delay(a=1.0, b=2.5):
    time.sleep(random.uniform(a, b))


def extract_price(text):
    if not text:
        return None
    cleaned = text.replace(".", "").replace(",", ".")
    match = re.search(r"(\d+(?:\.\d+)?)", cleaned)
    return float(match.group(1)) if match else None


def build_booking_search_url(region, checkin, checkout, adults=2, rooms=1, children=0):
    return (
        "https://www.booking.com/searchresults.de.html"
        f"?ss={quote_plus(region)}"
        f"&checkin={checkin}&checkout={checkout}"
        f"&group_adults={adults}&no_rooms={rooms}&group_children={children}"
    )


def scrape_booking_region(region, checkin, checkout, adults=2, max_results=5, headless=True):
    """
    Durchsucht Booking.com für eine Region/Stadt und einen Zeitraum und gibt
    eine Liste von Angeboten [{name, price, url}, ...] zurück, sortiert wie
    sie auf der Seite erscheinen (i.d.R. nach Relevanz/"Top-Auswahl").
    """
    url = build_booking_search_url(region, checkin, checkout, adults)
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = _new_context(browser)
        page = context.new_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            _human_delay()
            _accept_cookies(page)
            page.mouse.wheel(0, 800)
            _human_delay()

            cards = page.query_selector_all("div[data-testid='property-card']")
            for card in cards[:max_results]:
                name_el = card.query_selector("div[data-testid='title']")
                price_el = card.query_selector("span[data-testid='price-and-discounted-price']")
                link_el = card.query_selector("a[data-testid='title-link']")

                name = name_el.inner_text().strip() if name_el else None
                price_text = price_el.inner_text().strip() if price_el else None
                href = link_el.get_attribute("href") if link_el else None

                price = extract_price(price_text)
                if name and price is not None:
                    results.append({"name": name, "price": price, "url": href})
        finally:
            browser.close()

    return results
