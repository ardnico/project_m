from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Dict

from src.infra.ig_client import PriceSnapshot


SCHEMA = {
    "sessions": """
    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cst TEXT NOT NULL,
        security_token TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    "prices": """
    CREATE TABLE IF NOT EXISTS prices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        epic TEXT NOT NULL,
        bid REAL NOT NULL,
        ask REAL NOT NULL,
        mid REAL NOT NULL,
        timestamp TEXT NOT NULL
    );
    """,
}


def init_db(path: str) -> sqlite3.Connection:
    db_path = Path(path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL;")
    for statement in SCHEMA.values():
        conn.execute(statement)
    conn.commit()
    return conn


def store_session(conn: sqlite3.Connection, tokens: Dict[str, str]) -> None:
    conn.execute(
        "INSERT INTO sessions (cst, security_token) VALUES (?, ?)",
        (tokens.get("CST", ""), tokens.get("X-SECURITY-TOKEN", "")),
    )
    conn.commit()


def store_price(conn: sqlite3.Connection, snapshot: PriceSnapshot) -> None:
    conn.execute(
        "INSERT INTO prices (epic, bid, ask, mid, timestamp) VALUES (?, ?, ?, ?, ?)",
        (
            snapshot.epic,
            snapshot.bid,
            snapshot.ask,
            snapshot.mid,
            snapshot.timestamp.isoformat(),
        ),
    )
    conn.commit()


__all__ = ["init_db", "store_session", "store_price", "SCHEMA"]
