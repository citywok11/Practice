import os
import json
import time
from typing import Any, Dict, Iterator, List

import psycopg2
from psycopg2.extras import RealDictCursor


DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("POSTGRES_DB", os.getenv("DB_NAME", "travel"))
DB_USER = os.getenv("POSTGRES_USER", os.getenv("DB_USER", "travel"))
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", os.getenv("DB_PASSWORD", "travel"))


def _connect_with_retry(retries: int = 20, delay: float = 0.5):
    last_err = None
    for _ in range(retries):
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
            )
            conn.autocommit = True
            return conn
        except Exception as e:
            last_err = e
            time.sleep(delay)
    raise last_err


def _ensure_schema(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS destinations (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                country TEXT NOT NULL,
                attractions JSONB NOT NULL DEFAULT '[]'::jsonb
            );
            """
        )


def _seed_if_empty(conn) -> None:
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT COUNT(*) AS c FROM destinations;")
        count = cur.fetchone()["c"]
        if count and count > 0:
            return
        rows = [
            {"id": 1, "name": "Paris", "country": "France", "attractions": ["Eiffel Tower", "Louvre Museum"]},
            {"id": 2, "name": "Tokyo", "country": "Japan", "attractions": ["Shibuya Crossing", "Tokyo Tower"]},
            {"id": 3, "name": "New York City", "country": "USA", "attractions": ["Statue of Liberty", "Central Park"]},
        ]
        for r in rows:
            cur.execute(
                "INSERT INTO destinations (id, name, country, attractions) VALUES (%s, %s, %s, %s)"
                " ON CONFLICT (id) DO NOTHING;",
                (r["id"], r["name"], r["country"], json.dumps(r.get("attractions", []))),
            )


def _fetch_all(conn) -> List[Dict[str, Any]]:
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT id, name, country, attractions FROM destinations ORDER BY id ASC;")
        rows = cur.fetchall()
        # Ensure attractions is a native Python list
        cleaned = []
        for r in rows:
            cleaned.append(
                {
                    "id": int(r["id"]),
                    "name": r["name"],
                    "country": r["country"],
                    "attractions": r.get("attractions") if isinstance(r.get("attractions"), list) else json.loads(r.get("attractions", "[]")),
                }
            )
        return cleaned


class _DestinationsList(list):
    """A minimal list subclass backed by Postgres.

    By subclassing list, Flask's jsonify can serialize it directly.
    append(item) writes to the DB and refreshes the in-memory list.
    """

    def __init__(self) -> None:
        self._conn = _connect_with_retry()
        _ensure_schema(self._conn)
        _seed_if_empty(self._conn)
        data = _fetch_all(self._conn)
        super().__init__(data)

    def _reload(self) -> None:
        data = _fetch_all(self._conn)
        self.clear()
        super().extend(data)

    def append(self, item: Dict[str, Any]) -> None:  # type: ignore[override]
        # Expecting fields: id (int), name (str), country (str), attractions (list)
        with self._conn.cursor() as cur:
            cur.execute(
                "INSERT INTO destinations (id, name, country, attractions) VALUES (%s, %s, %s, %s)"
                " ON CONFLICT (id) DO NOTHING;",
                (
                    int(item.get("id")),
                    item.get("name"),
                    item.get("country"),
                    json.dumps(item.get("attractions", [])),
                ),
            )
        self._reload()

    def delete(self, id: int) -> None:
        with self._conn.cursor() as cur:
            cur.execute("DELETE FROM destinations WHERE id = %s;", (id,))
        self._reload()


# Expose the list-like object expected by main.py
destinations = _DestinationsList()
