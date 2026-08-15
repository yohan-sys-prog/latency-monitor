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

    def time_series_for_target(self, target: str, hours: int = 24, limit: int = 100):
        """Fetch time-series latency data for graphing."""
        since = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        with self.store._connect() as conn:
            rows = conn.execute(
                "SELECT value, success, created_at FROM measurements WHERE target = ? AND created_at >= ? ORDER BY created_at DESC LIMIT ?",
                (target, since, limit),
            ).fetchall()
        return [dict(row) for row in reversed(rows)]  # oldest first

    def latest_recovery(self, target: str):
        """Get the most recent incident and check if target has recovered."""
        with self.store._connect() as conn:
            incident = conn.execute(
                "SELECT * FROM incidents WHERE target = ? ORDER BY created_at DESC LIMIT 1",
                (target,),
            ).fetchone()
            if incident is None:
                return None
            
            incident_dict = dict(incident)
            incident_time = incident_dict["created_at"]
            
            # Check if there are successful pings after the incident
            recovery = conn.execute(
                "SELECT created_at FROM measurements WHERE target = ? AND success = 1 AND created_at > ? ORDER BY created_at ASC LIMIT 1",
                (target, incident_time),
            ).fetchone()
            
            return {
                "incident": incident_dict,
                "recovered_at": dict(recovery)["created_at"] if recovery else None,
            }
