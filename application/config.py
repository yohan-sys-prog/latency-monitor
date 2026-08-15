import json
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_TARGETS = ["8.8.8.8", "1.1.1.1"]


@dataclass
class MonitorConfig:
    targets: list[str] = field(default_factory=lambda: DEFAULT_TARGETS.copy())
    interval: float = 1.0
    ping_timeout: float = 1.0
    latency_threshold_ms: float = 200.0
    packet_loss_threshold: float = 10.0
    alert_cooldown_seconds: int = 60
    data_retention_days: int = 30
    db_path: str = "data/latency.db"
    dashboard_host: str = "0.0.0.0"
    dashboard_port: int = 8000
    notification_config_path: str = "notification_config.json"

    def to_dict(self) -> dict:
        return {
            "targets": self.targets,
            "interval": self.interval,
            "ping_timeout": self.ping_timeout,
            "latency_threshold_ms": self.latency_threshold_ms,
            "packet_loss_threshold": self.packet_loss_threshold,
            "alert_cooldown_seconds": self.alert_cooldown_seconds,
            "data_retention_days": self.data_retention_days,
            "db_path": self.db_path,
            "dashboard_host": self.dashboard_host,
            "dashboard_port": self.dashboard_port,
            "notification_config_path": self.notification_config_path,
        }

    def save(self, path: str | Path) -> None:
        save_path = Path(path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        save_path.write_text(json.dumps(self.to_dict(), indent=2) + "\n", encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "MonitorConfig":
        config_path = Path(path)
        if not config_path.exists():
            config = cls()
            config.save(config_path)
            return config

        data = json.loads(config_path.read_text(encoding="utf-8"))
        return cls(
            targets=data.get("targets", DEFAULT_TARGETS),
            interval=float(data.get("interval", 1.0)),
            ping_timeout=float(data.get("ping_timeout", 1.0)),
            latency_threshold_ms=float(data.get("latency_threshold_ms", 200.0)),
            packet_loss_threshold=float(data.get("packet_loss_threshold", 10.0)),
            alert_cooldown_seconds=int(data.get("alert_cooldown_seconds", 60)),
            data_retention_days=int(data.get("data_retention_days", 30)),
            db_path=data.get("db_path", "data/latency.db"),
            dashboard_host=data.get("dashboard_host", "0.0.0.0"),
            dashboard_port=int(data.get("dashboard_port", 8000)),
            notification_config_path=data.get("notification_config_path", "notification_config.json"),
        )


def load_config(path: str | Path = "monitor_config.json") -> MonitorConfig:
    return MonitorConfig.load(path)

