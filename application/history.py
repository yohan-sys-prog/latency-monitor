from datetime import datetime, timedelta


class HistoryQuery:
    def __init__(self, store):
        self.store = store

    def average_for_period(self, target: str, hours: int = 24):
        since = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        rows = self.store._connect().execute(
            "SELECT AVG(value) AS avg_value FROM measurements WHERE target = ? AND success = 1 AND created_at >= ?",
            (target, since),
        ).fetchone()
        return None if rows is None or rows["avg_value"] is None else float(rows["avg_value"])

    def incidents_for_target(self, target: str, limit: int = 20):
        rows = self.store._connect().execute(
            "SELECT * FROM incidents WHERE target = ? ORDER BY created_at DESC LIMIT ?",
            (target, limit),
        ).fetchall()
        return [dict(row) for row in rows]
