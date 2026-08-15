from datetime import datetime, timezone


class AlertManager:
    def __init__(self, store):
        self.store = store
        self.last_alert_at = {}

    def evaluate(self, target: str, metrics: dict, latency_threshold_ms: float, packet_loss_threshold: float, cooldown_seconds: int = 60):
        current = metrics.get("current")
        packet_loss = metrics.get("packet_loss_percent", 0.0)
        if current is None and packet_loss >= packet_loss_threshold:
            return self._record_alert(target, f"Connection down for {target}", "critical", cooldown_seconds)

        if current is not None and current > latency_threshold_ms:
            return self._record_alert(target, f"High latency for {target}: {current}ms", "warning", cooldown_seconds)

        if packet_loss >= packet_loss_threshold:
            return self._record_alert(target, f"Packet loss elevated for {target}: {packet_loss}%", "warning", cooldown_seconds)

        return None

    def _record_alert(self, target: str, message: str, severity: str, cooldown_seconds: int):
        now = datetime.now(timezone.utc)
        last = self.last_alert_at.get(target)
        if last is not None and (now - last).total_seconds() < cooldown_seconds:
            return None
        self.last_alert_at[target] = now
        self.store.record_incident(target, message, severity=severity)
        return {"target": target, "message": message, "severity": severity, "timestamp": now.isoformat()}
