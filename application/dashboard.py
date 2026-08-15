from pathlib import Path
import os

from flask import Flask, jsonify, render_template

from application.alerts import AlertManager
from application.config import load_config
from application.history import HistoryQuery
from application.monitor import PingMonitor
from application.storage import MeasurementStore


def create_app(config_path: str | Path = "monitor_config.json") -> Flask:
    config = load_config(config_path)
    port = int(os.getenv("LATENCY_MONITOR_PORT", config.dashboard_port))
    config.dashboard_port = port
    store = MeasurementStore(config.db_path)
    monitor = PingMonitor(config.targets, interval=config.interval, store=store)
    alert_manager = AlertManager(store)
    history = HistoryQuery(store)

    app = Flask(
        __name__,
        template_folder=str(Path(__file__).resolve().parent.parent / "templates"),
        static_folder=str(Path(__file__).resolve().parent.parent / "static"),
    )

    @app.route("/")
    def index():
        return render_template("dashboard.html", targets=config.targets)

    @app.route("/api/status")
    def api_status():
        snapshot = monitor.run_once()
        alerts = []
        for target, metrics in snapshot.items():
            alert = alert_manager.evaluate(
                target,
                metrics,
                config.latency_threshold_ms,
                config.packet_loss_threshold,
                config.alert_cooldown_seconds,
            )
            if alert is not None:
                alerts.append(alert)

        incident_rows = []
        for target in config.targets:
            incident_rows.extend(history.incidents_for_target(target, limit=10))
        incident_rows.sort(key=lambda item: item.get("created_at", ""), reverse=True)

        return jsonify({
            "targets": snapshot,
            "alerts": alerts,
            "incidents": incident_rows[:10],
            "config": {
                "interval": config.interval,
                "latency_threshold_ms": config.latency_threshold_ms,
                "packet_loss_threshold": config.packet_loss_threshold,
            },
        })

    @app.route("/api/history/<target>")
    def api_history(target: str):
        return jsonify({
            "target": target,
            "average_24h": history.average_for_period(target, hours=24),
            "measurements": history.store.get_recent_measurements(target, limit=50),
        })

    @app.route("/api/incidents")
    def api_incidents():
        rows = []
        for target in config.targets:
            rows.extend(history.incidents_for_target(target, limit=20))
        rows.sort(key=lambda item: item.get("created_at", ""), reverse=True)
        return jsonify({"incidents": rows[:20]})

    return app


app = create_app()


if __name__ == "__main__":
    config = load_config()
    port = int(os.getenv("LATENCY_MONITOR_PORT", config.dashboard_port))
    app.run(host=config.dashboard_host, port=port, debug=True)
