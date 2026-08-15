"""
Multi-channel notification system for latency monitoring alerts.
Supports: email, webhooks (Discord/Slack), and local notifications.
"""

import json
import smtplib
import urllib.request
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional


@dataclass
class EmailConfig:
    enabled: bool = False
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    sender_email: str = ""
    sender_password: str = ""
    recipient_emails: list[str] = None

    def __post_init__(self):
        if self.recipient_emails is None:
            self.recipient_emails = []


@dataclass
class WebhookConfig:
    enabled: bool = False
    url: str = ""
    platform: str = "discord"  # discord, slack, custom
    include_timestamp: bool = True
    include_target: bool = True
    include_severity: bool = True


@dataclass
class NotificationConfig:
    email: EmailConfig = None
    webhook: WebhookConfig = None

    def __post_init__(self):
        if self.email is None:
            self.email = EmailConfig()
        if self.webhook is None:
            self.webhook = WebhookConfig()

    @classmethod
    def load(cls, path: str | Path) -> "NotificationConfig":
        config_path = Path(path)
        if not config_path.exists():
            return cls()

        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
            email_data = data.get("email", {})
            webhook_data = data.get("webhook", {})

            return cls(
                email=EmailConfig(**email_data) if email_data else EmailConfig(),
                webhook=WebhookConfig(**webhook_data) if webhook_data else WebhookConfig(),
            )
        except Exception:
            return cls()

    def save(self, path: str | Path) -> None:
        config_path = Path(path)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "email": {
                "enabled": self.email.enabled,
                "smtp_host": self.email.smtp_host,
                "smtp_port": self.email.smtp_port,
                "sender_email": self.email.sender_email,
                "recipient_emails": self.email.recipient_emails,
            },
            "webhook": {
                "enabled": self.webhook.enabled,
                "url": self.webhook.url,
                "platform": self.webhook.platform,
                "include_timestamp": self.webhook.include_timestamp,
                "include_target": self.webhook.include_target,
                "include_severity": self.webhook.include_severity,
            },
        }
        config_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


class NotificationChannel(ABC):
    """Abstract base class for notification channels."""

    @abstractmethod
    def send(
        self, target: str, message: str, severity: str, timestamp: Optional[str] = None
    ) -> bool:
        """Send notification. Returns True on success."""
        pass


class EmailNotifier(NotificationChannel):
    """Send alerts via email."""

    def __init__(self, config: EmailConfig):
        self.config = config

    def send(
        self, target: str, message: str, severity: str, timestamp: Optional[str] = None
    ) -> bool:
        if not self.config.enabled or not self.config.recipient_emails:
            return True

        try:
            subject = f"[{severity.upper()}] Network Alert: {target}"
            body = f"Target: {target}\nSeverity: {severity}\nMessage: {message}"

            if timestamp:
                body += f"\nTime: {timestamp}"

            msg = MIMEText(body)
            msg["Subject"] = subject
            msg["From"] = self.config.sender_email
            msg["To"] = ", ".join(self.config.recipient_emails)

            with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port) as server:
                server.starttls()
                server.login(self.config.sender_email, self.config.sender_password)
                server.send_message(msg)

            return True
        except Exception as e:
            print(f"Email notification failed: {e}")
            return False


class WebhookNotifier(NotificationChannel):
    """Send alerts via webhooks (Discord, Slack, etc)."""

    def __init__(self, config: WebhookConfig):
        self.config = config

    def send(
        self, target: str, message: str, severity: str, timestamp: Optional[str] = None
    ) -> bool:
        if not self.config.enabled or not self.config.url:
            return True

        try:
            if self.config.platform == "discord":
                payload = self._build_discord_payload(target, message, severity, timestamp)
            elif self.config.platform == "slack":
                payload = self._build_slack_payload(target, message, severity, timestamp)
            else:
                payload = self._build_generic_payload(target, message, severity, timestamp)

            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                self.config.url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=5) as response:
                return response.status == 204 or response.status == 200

        except Exception as e:
            print(f"Webhook notification failed: {e}")
            return False

    def _build_discord_payload(
        self, target: str, message: str, severity: str, timestamp: Optional[str]
    ) -> dict:
        """Build Discord embed payload."""
        color_map = {"critical": 15158332, "warning": 15105570, "info": 3447003}
        color = color_map.get(severity.lower(), 3447003)

        embed = {
            "title": f"{severity.upper()}: {target}",
            "description": message,
            "color": color,
            "fields": [],
        }

        if self.config.include_target:
            embed["fields"].append({"name": "Target", "value": target, "inline": True})

        if self.config.include_severity:
            embed["fields"].append(
                {"name": "Severity", "value": severity.upper(), "inline": True}
            )

        if self.config.include_timestamp and timestamp:
            embed["fields"].append({"name": "Time", "value": timestamp, "inline": False})

        return {"embeds": [embed]}

    def _build_slack_payload(
        self, target: str, message: str, severity: str, timestamp: Optional[str]
    ) -> dict:
        """Build Slack message payload."""
        color_map = {"critical": "danger", "warning": "warning", "info": "good"}
        color = color_map.get(severity.lower(), "good")

        blocks = [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*{severity.upper()}*\n{message}"},
            }
        ]

        fields = []
        if self.config.include_target:
            fields.append({"type": "mrkdwn", "text": f"*Target:*\n{target}"})

        if self.config.include_severity:
            fields.append(
                {"type": "mrkdwn", "text": f"*Severity:*\n{severity.upper()}"}
            )

        if fields:
            blocks.append({"type": "section", "fields": fields})

        if self.config.include_timestamp and timestamp:
            blocks.append(
                {
                    "type": "context",
                    "elements": [{"type": "mrkdwn", "text": f"_Time: {timestamp}_"}],
                }
            )

        return {"blocks": blocks}

    def _build_generic_payload(
        self, target: str, message: str, severity: str, timestamp: Optional[str]
    ) -> dict:
        """Build generic JSON payload."""
        payload = {
            "target": target,
            "message": message,
            "severity": severity,
        }

        if timestamp:
            payload["timestamp"] = timestamp

        return payload


class NotificationManager:
    """Coordinate multi-channel alert notifications."""

    def __init__(self, config: NotificationConfig):
        self.config = config
        self.email_notifier = EmailNotifier(config.email)
        self.webhook_notifier = WebhookNotifier(config.webhook)

    def notify(
        self, target: str, message: str, severity: str = "warning"
    ) -> dict[str, bool]:
        """Send notification through all enabled channels. Returns success status per channel."""
        timestamp = datetime.now(timezone.utc).isoformat()

        results = {}

        if self.config.email.enabled:
            results["email"] = self.email_notifier.send(target, message, severity, timestamp)

        if self.config.webhook.enabled:
            results["webhook"] = self.webhook_notifier.send(
                target, message, severity, timestamp
            )

        return results
