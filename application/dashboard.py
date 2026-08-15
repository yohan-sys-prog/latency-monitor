from pathlib import Path
import os

from flask import Flask, jsonify, render_template

from application.alerts import AlertManager
from application.config import load_config
from application.history import HistoryQuery
from application.monitor import PingMonitor
from application.notifications import NotificationConfig, NotificationManager
from application.storage import MeasurementStore


def create_app(config_path: str | Path = "monitor_config.json") -> Flask:
    config = load_config(config_path)
    port = int(os.getenv("LATENCY_MONITOR_PORT", config.dashboard_port))
    config.dashboard_port = port
    store = MeasurementStore(config.db_path)
    monitor = PingMonitor(config.targets, interval=config.interval, store=store)
    alert_manager = AlertManager(store)
    history = HistoryQuery(store)
    notification_config = NotificationConfig.load(config.notification_config_path)
    notification_manager = NotificationManager(notification_config)

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
                # Send notifications for this alert
                notification_manager.notify(
                    target,
                    alert["message"],
                    alert["severity"],
                )

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

    @app.route("/api/graph/<target>")
    def api_graph(target: str):
        """Fetch time-series data for a target for graphing."""
        if target not in config.targets:
            return jsonify({"error": "target not found"}), 404
        
        series = history.time_series_for_target(target, hours=24, limit=100)
        recovery = history.latest_recovery(target)
        
        return jsonify({
            "target": target,
            "series": series,
            "recovery": recovery,
        })

    @app.route("/api/notifications/config", methods=["GET"])
    def api_notifications_config():
        """Get current notification configuration."""
        return jsonify({
            "email": {
                "enabled": notification_config.email.enabled,
                "smtp_host": notification_config.email.smtp_host,
                "smtp_port": notification_config.email.smtp_port,
                "sender_email": notification_config.email.sender_email,
                "recipient_emails": notification_config.email.recipient_emails,
            },
            "webhook": {
                "enabled": notification_config.webhook.enabled,
                "url": notification_config.webhook.url,
                "platform": notification_config.webhook.platform,
            },
        })

    @app.route("/api/notifications/test", methods=["POST"])
    def api_notifications_test():
        """Send a test notification to verify configuration."""
        results = notification_manager.notify(
            "test-target",
            "This is a test notification from the Latency Monitor.",
            "warning",
        )
        return jsonify({"results": results})

    return app


app = create_app()


if __name__ == "__main__":
    config = load_config()
    port = int(os.getenv("LATENCY_MONITOR_PORT", config.dashboard_port))
    app.run(host=config.dashboard_host, port=port, debug=True)
