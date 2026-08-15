from pathlib import Path
import os
from functools import wraps

from flask import Flask, jsonify, render_template, request

from application.alerts import AlertManager
from application.auth import AuthenticationManager
from application.api import api_response, rate_limit, validate_json
from application.config import load_config
from application.history import HistoryQuery
from application.monitor import PingMonitor
from application.notifications import NotificationConfig, NotificationManager
from application.storage import MeasurementStore


def require_token(f):
    """Decorator to require valid JWT token for route access."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        global auth_manager
        
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if not token:
            return jsonify({"error": "Missing authorization token"}), 401
        
        payload = auth_manager.verify_token(token)
        if not payload:
            return jsonify({"error": "Invalid or expired token"}), 401
        
        # Make user info available to the route
        request.user = payload
        return f(*args, **kwargs)
    return decorated_function


def create_app(config_path: str | Path = "monitor_config.json") -> Flask:
    global auth_manager
    
    config = load_config(config_path)
    port = int(os.getenv("LATENCY_MONITOR_PORT", config.dashboard_port))
    config.dashboard_port = port
    store = MeasurementStore(config.db_path)
    monitor = PingMonitor(config.targets, interval=config.interval, store=store)
    alert_manager = AlertManager(store)
    history = HistoryQuery(store)
    notification_config = NotificationConfig.load(config.notification_config_path)
    notification_manager = NotificationManager(notification_config)
    auth_manager = AuthenticationManager()

    app = Flask(
        __name__,
        template_folder=str(Path(__file__).resolve().parent.parent / "templates"),
        static_folder=str(Path(__file__).resolve().parent.parent / "static"),
    )

    # Add CORS headers
    @app.after_request
    def add_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        return response

    # Error handlers for production-grade API
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"status": "error", "error": "Endpoint not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"status": "error", "error": "Internal server error"}), 500

    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({"status": "error", "error": "Unauthorized"}), 401

    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({"status": "error", "error": "Forbidden"}), 403

    @app.route("/")
    def index():
        return render_template("dashboard.html", targets=config.targets)

    @app.route("/api/auth/login", methods=["POST"])
    @rate_limit(max_requests=10, window_seconds=60)
    @validate_json("username", "password")
    def api_auth_login():
        """Authenticate a user and return a JWT token."""
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")

        token = auth_manager.authenticate(username, password)
        if not token:
            return api_response(error="Invalid credentials", status=401)

        return api_response({
            "token": token,
            "message": "Login successful",
        })

    @app.route("/api/auth/verify", methods=["GET"])
    @require_token
    def api_auth_verify():
        """Verify current authentication token."""
        return jsonify({
            "valid": True,
            "user": request.user["username"],
            "role": request.user["role"],
        })

    @app.route("/api/auth/change-password", methods=["POST"])
    @require_token
    def api_auth_change_password():
        """Change the current user's password."""
        data = request.get_json() or {}
        old_password = data.get("old_password")
        new_password = data.get("new_password")

        if not old_password or not new_password:
            return jsonify({"error": "Missing old or new password"}), 400

        username = request.user["username"]
        if auth_manager.change_password(username, old_password, new_password):
            return jsonify({"message": "Password changed successfully"})
        else:
            return jsonify({"error": "Invalid old password"}), 401

    @app.route("/api/auth/users", methods=["GET"])
    @require_token
    def api_auth_users():
        """List all users (admin only)."""
        if request.user["role"] != "admin":
            return jsonify({"error": "Admin access required"}), 403

        users = auth_manager.user_store.list_users()
        return jsonify({
            "users": [
                {
                    "username": u.username,
                    "role": u.role,
                    "created_at": u.created_at,
                    "last_login": u.last_login,
                }
                for u in users
            ]
        })

    @app.route("/api/auth/users", methods=["POST"])
    @require_token
    def api_auth_create_user():
        """Create a new user (admin only)."""
        if request.user["role"] != "admin":
            return jsonify({"error": "Admin access required"}), 403

        data = request.get_json() or {}
        username = data.get("username")
        password = data.get("password")
        role = data.get("role", "user")

        if not username or not password:
            return jsonify({"error": "Missing username or password"}), 400

        try:
            user = auth_manager.create_user(username, password, admin_only=(role == "admin"))
            return jsonify({
                "message": f"User {username} created successfully",
                "user": {
                    "username": user.username,
                    "role": user.role,
                    "created_at": user.created_at,
                },
            }), 201
        except ValueError as e:
            return jsonify({"error": str(e)}), 409

    @app.route("/api/status")
    @require_token
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
    @require_token
    def api_history(target: str):
        return jsonify({
            "target": target,
            "average_24h": history.average_for_period(target, hours=24),
            "measurements": history.store.get_recent_measurements(target, limit=50),
        })

    @app.route("/api/incidents")
    @require_token
    def api_incidents():
        rows = []
        for target in config.targets:
            rows.extend(history.incidents_for_target(target, limit=20))
        rows.sort(key=lambda item: item.get("created_at", ""), reverse=True)
        return jsonify({"incidents": rows[:20]})

    @app.route("/api/graph/<target>")
    @require_token
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
    @require_token
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
    @require_token
    def api_notifications_test():
        """Send a test notification to verify configuration."""
        results = notification_manager.notify(
            "test-target",
            "This is a test notification from the Latency Monitor.",
            "warning",
        )
        return jsonify({"results": results})

    # V1 API endpoints (production-grade versioning)
    @app.route("/api/v1/status", methods=["GET"])
    @require_token
    @rate_limit(max_requests=60, window_seconds=60)
    def api_v1_status():
        """Get current system status (V1 API)."""
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
                notification_manager.notify(
                    target,
                    alert["message"],
                    alert["severity"],
                )

        return api_response({
            "targets": snapshot,
            "alerts": alerts,
            "config": {
                "interval": config.interval,
                "latency_threshold_ms": config.latency_threshold_ms,
                "packet_loss_threshold": config.packet_loss_threshold,
            },
        })

    @app.route("/api/v1/health", methods=["GET"])
    def api_v1_health():
        """Health check endpoint (no auth required)."""
        return api_response({
            "status": "healthy",
            "version": "1.0.0",
        })

    return app


app = create_app()


if __name__ == "__main__":
    config = load_config()
    port = int(os.getenv("LATENCY_MONITOR_PORT", config.dashboard_port))
    app.run(host=config.dashboard_host, port=port, debug=True)
