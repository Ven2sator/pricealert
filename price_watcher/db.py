"""
db.py – SQLite-Anbindung für den Preisalarm.

Legt zwei Tabellen an:
- price_checks: jede einzelne Preisabfrage (auch ohne Alarm)
- alerts:       nur die Treffer, bei denen der Zielpreis erreicht wurde
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.expanduser("~/price_watcher.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS price_checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    watch_name TEXT NOT NULL,
    region TEXT,
    source TEXT NOT NULL,
    listing_name TEXT,
    price REAL,
    url TEXT
);

CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    watch_name TEXT NOT NULL,
    region TEXT,
    listing_name TEXT,
    price REAL,
    target_price REAL,
    url TEXT
);
"""


def get_connection(db_path=None):
    conn = sqlite3.connect(db_path or DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def init_db(db_path=None):
    conn = get_connection(db_path)
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def log_price_check(watch_name, region, source, listing_name, price, url, db_path=None):
    conn = get_connection(db_path)
    conn.execute(
        "INSERT INTO price_checks (timestamp, watch_name, region, source, listing_name, price, url) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (_now(), watch_name, region, source, listing_name, price, url),
    )
    conn.commit()
    conn.close()


def log_alert(watch_name, region, listing_name, price, target_price, url, db_path=None):
    conn = get_connection(db_path)
    conn.execute(
        "INSERT INTO alerts (timestamp, watch_name, region, listing_name, price, target_price, url) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (_now(), watch_name, region, listing_name, price, target_price, url),
    )
    conn.commit()
    conn.close()
