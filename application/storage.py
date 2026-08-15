import sqlite3
from datetime import datetime, timezone
from pathlib import Path


class MeasurementStore:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS targets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS measurements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    target TEXT NOT NULL,
                    value REAL,
                    success INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS incidents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    target TEXT NOT NULL,
                    message TEXT NOT NULL,
                    severity TEXT NOT NULL DEFAULT 'warning',
                    duration_seconds INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_measurements_target_created ON measurements(target, created_at)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_incidents_target_created ON incidents(target, created_at)"
            )
            conn.commit()

    def ensure_target(self, target: str) -> None:
        with self._connect() as conn:
            conn.execute("INSERT OR IGNORE INTO targets (name) VALUES (?)", (target,))
            conn.commit()

    def record_measurement(self, target: str, value: float | None, success: bool = True) -> None:
        self.ensure_target(target)
        timestamp = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO measurements (target, value, success, created_at) VALUES (?, ?, ?, ?)",
                (target, value, int(success), timestamp),
            )
            conn.commit()

    def record_incident(self, target: str, message: str, severity: str = "warning", duration_seconds: int = 0) -> None:
        self.ensure_target(target)
        timestamp = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO incidents (target, message, severity, duration_seconds, created_at) VALUES (?, ?, ?, ?, ?)",
                (target, message, severity, duration_seconds, timestamp),
            )
            conn.commit()

    def get_recent_measurements(self, target: str, limit: int = 20):
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT value, success, created_at FROM measurements WHERE target = ? ORDER BY created_at DESC LIMIT ?",
                (target, limit),
            ).fetchall()
            return [dict(row) for row in rows]

    def get_average_latency(self, target: str):
        with self._connect() as conn:
            row = conn.execute(
                "SELECT AVG(value) AS avg_value FROM measurements WHERE target = ? AND success = 1",
                (target,),
            ).fetchone()
            return None if row is None or row["avg_value"] is None else float(row["avg_value"])

    def get_failure_count(self, target: str):
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS failed FROM measurements WHERE target = ? AND success = 0",
                (target,),
            ).fetchone()
            return 0 if row is None else int(row["failed"])
