# latency-monitor

A production-ready multi-target network monitoring application with live dashboards, alerts, authentication, and Docker support.

## Features

- **Multi-target monitoring**: Track multiple network targets simultaneously
- **Live dashboard**: Real-time metrics with automatic refresh
- **Latency graphs**: Chart.js-powered historical latency visualization
- **Packet loss tracking**: Monitor and alert on packet loss percentage
- **Recovery detection**: Automatic detection of target recovery after outages
- **Incident tracking**: SQLite-based incident and measurement persistence
- **Multi-channel alerts**: Email and webhook (Discord/Slack) notifications
- **User authentication**: JWT-based authentication with role-based access control
- **Production API**: Versioned REST API with rate limiting and CORS support
- **CLI monitoring**: Terminal-based monitoring mode
- **Docker deployment**: Production-grade Docker setup with health checks

## Quick start

### Local development

Run the dashboard:

```bash
python3 -m application.dashboard
```

Open http://localhost:8000 and login with default credentials:
- Username: `admin`
- Password: `admin` (change this immediately!)

Run the CLI monitor:

```bash
python3 -m application.cli --targets 8.8.8.8 1.1.1.1 --interval 1.0
```

### Docker deployment

```bash
docker compose up
```

The app will be available at http://localhost:8000

## Configuration

### Main config (`monitor_config.json`)

- `targets`: List of IPs/hostnames to monitor
- `interval`: Ping interval in seconds
- `latency_threshold_ms`: Alert threshold for high latency
- `packet_loss_threshold`: Alert threshold for packet loss %
- `alert_cooldown_seconds`: Cooldown between duplicate alerts
- `dashboard_port`: Web server port

### Notification config (`notification_config.json`)

```json
{
  "email": {
    "enabled": false,
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "your-email@gmail.com",
    "recipient_emails": ["alert@example.com"]
  },
  "webhook": {
    "enabled": false,
    "url": "https://discord.com/api/webhooks/...",
    "platform": "discord"
  }
}
```

## API

### Authentication

```bash
# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}'

# Response includes JWT token
```

### V1 API Endpoints

All endpoints require `Authorization: Bearer <token>` header (except `/api/v1/health`):

- `GET /api/v1/health` - Health check
- `GET /api/v1/status` - Current system status
- `GET /api/status` - Current metrics (legacy)
- `GET /api/history/<target>` - Target history
- `GET /api/graph/<target>` - Time-series data for graphing
- `GET /api/incidents` - Recent incidents
- `POST /api/auth/change-password` - Change password

## Architecture

The application is organized into modular components:

- `monitor.py`: Multi-target ping engine
- `storage.py`: SQLite persistence layer
- `alerts.py`: Alert evaluation logic
- `notifications.py`: Email/webhook notifications
- `history.py`: Historical data queries
- `auth.py`: User management and JWT auth
- `api.py`: Production API utilities
- `dashboard.py`: Flask web application
- `cli.py`: Terminal interface

## Docker

### Environment variables

- `LATENCY_MONITOR_PORT`: Dashboard port (default: 8000)
- `LATENCY_MONITOR_HOST`: Dashboard host (default: 0.0.0.0)
- `PYTHONUNBUFFERED`: Always set to 1

### Volumes

- `/app/data`: Persistent data directory
- `/app/monitor_config.json`: Configuration file
- `/app/notification_config.json`: Notification config

### Health check

The container includes a built-in health check via `/api/v1/health`.

## Development

Run tests:

```bash
python3 -m unittest discover -s tests -v
```

## License

MIT