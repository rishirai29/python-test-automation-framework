"""Direct SQLite access used for backend / database validation in tests."""
import sqlite3


class Database:
    def __init__(self, path: str):
        self.path = path

    def _connect(self):
        conn = sqlite3.connect(self.path, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def query(self, sql: str, params=()) -> list[dict]:
        conn = self._connect()
        try:
            return [dict(r) for r in conn.execute(sql, params).fetchall()]
        finally:
            conn.close()

    def scalar(self, sql: str, params=()):
        rows = self.query(sql, params)
        return next(iter(rows[0].values())) if rows else None

    def execute(self, sql: str, params=()) -> None:
        conn = self._connect()
        try:
            conn.execute(sql, params)
            conn.commit()
        finally:
            conn.close()
