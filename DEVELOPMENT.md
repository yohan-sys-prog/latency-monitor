# Development Guide

This guide covers development setup, architecture, and practices for latency-monitor contributors.

## Table of Contents

1. [Development Environment](#development-environment)
2. [Architecture Overview](#architecture-overview)
3. [Module Guide](#module-guide)
4. [Testing](#testing)
5. [Debugging](#debugging)
6. [Performance](#performance)
7. [Common Tasks](#common-tasks)

## Development Environment

### Prerequisites

- Python 3.10+
- Git
- pip
- Virtual environment tool (venv)

### Quick Setup

```bash
# Clone repository
git clone https://github.com/yohan-sys-prog/latency-monitor.git
cd latency-monitor

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies and dev tools
pip install -r requirements.txt
pip install pytest pylint flake8 coverage
```

### Running the Application

```bash
# Development mode (auto-reload disabled)
python3 -m application.dashboard

# With custom port
LATENCY_MONITOR_PORT=9000 python3 -m application.dashboard

# CLI mode
python3 -m application.cli --targets 8.8.8.8 1.1.1.1 --interval 1.0
```

## Architecture Overview

The application follows a **layered architecture** with clear separation of concerns:

```
┌─────────────────────────────────────┐
│    Presentation (Flask Routes)      │
│    dashboard.py                     │
└────────────────┬────────────────────┘
                 │
┌─────────────────▼────────────────────┐
│      API Layer (api.py)              │
│  Response formatting, Rate limiting  │
└────────────────┬────────────────────┘
                 │
┌─────────────────▼────────────────────┐
│   Business Logic Layer               │
│  alerts.py, history.py, auth.py      │
└────────────────┬────────────────────┘
                 │
┌─────────────────▼────────────────────┐
│    Monitor & Storage Layer           │
│  monitor.py, storage.py, config.py   │
└─────────────────────────────────────┘
```

### Data Flow

1. **PingMonitor** executes pings and collects metrics
2. **MeasurementStore** persists data to SQLite
3. **AlertManager** evaluates conditions against thresholds
4. **NotificationManager** sends alerts via configured channels
5. **HistoryQuery** retrieves data for visualization
6. **Flask Routes** serve data via REST API
7. **Dashboard.html** displays real-time metrics

## Module Guide

### application/monitor.py

The core ping monitoring engine.

**Key Classes:**
- `PingMonitor`: Main monitor class

**Key Methods:**
- `run_once()`: Execute one monitoring cycle for all targets
- `_ping_once(target)`: Execute single ping via subprocess
- `_packet_loss_percent(target)`: Calculate failure rate

**Usage:**
```python
from application.monitor import PingMonitor
from application.storage import MeasurementStore

store = MeasurementStore('data/latency.db')
monitor = PingMonitor(['8.8.8.8', '1.1.1.1'], interval=2.0, store=store)

# Run one cycle
metrics = monitor.run_once()
print(metrics)  # {'8.8.8.8': {'current': 25.5, 'avg': 26.1, ...}, ...}
```

### application/storage.py

SQLite persistence layer for measurements and incidents.

**Key Classes:**
- `MeasurementStore`: Manages database operations

**Key Methods:**
- `record_measurement(target, value, success)`: Save ping result
- `record_incident(target, message, severity)`: Log alert event
- `get_recent_measurements(target, limit)`: Fetch time-series data

**Database Schema:**
```sql
CREATE TABLE targets (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE measurements (
    id INTEGER PRIMARY KEY,
    target TEXT NOT NULL,
    value REAL,
    success BOOLEAN,
    created_at TEXT
);

CREATE TABLE incidents (
    id INTEGER PRIMARY KEY,
    target TEXT NOT NULL,
    message TEXT,
    severity TEXT,
    duration_seconds REAL,
    created_at TEXT
);
```

### application/config.py

Configuration management with JSON persistence.

**Key Classes:**
- `MonitorConfig`: Configuration dataclass

**Configuration Keys:**
- `targets`: List of IPs/hostnames to monitor
- `interval`: Ping interval in seconds
- `latency_threshold_ms`: Alert threshold for high latency
- `packet_loss_threshold`: Alert threshold for packet loss %
- `alert_cooldown_seconds`: Cooldown between duplicate alerts

**Usage:**
```python
from application.config import MonitorConfig

config = MonitorConfig.load('monitor_config.json')
config.targets.append('9.9.9.9')
config.save('monitor_config.json')
```

### application/alerts.py

Alert evaluation and incident tracking.

**Key Classes:**
- `AlertManager`: Evaluates network conditions

**Key Methods:**
- `evaluate(target, metrics, latency_threshold_ms, packet_loss_threshold, cooldown_seconds)`: Check conditions

**Alert Types:**
- High latency detected
- High packet loss detected
- Both high latency and packet loss

**Usage:**
```python
from application.alerts import AlertManager

alert_mgr = AlertManager()
alert = alert_mgr.evaluate(
    target='8.8.8.8',
    metrics={'current': 150, 'avg': 140, 'packet_loss_percent': 5},
    latency_threshold_ms=100,
    packet_loss_threshold=10,
    cooldown_seconds=300
)
if alert:
    print(f"Alert: {alert['reason']}")
```

### application/history.py

Historical data queries and recovery detection.

**Key Classes:**
- `HistoryQuery`: Query historical data

**Key Methods:**
- `time_series_for_target(target, hours=24, limit=100)`: Get time-series data
- `latest_recovery(target)`: Detect recovery after outage
- `average_for_period(target, hours=24)`: Calculate average latency

**Usage:**
```python
from application.history import HistoryQuery

history = HistoryQuery(store)
data = history.time_series_for_target('8.8.8.8', hours=24)
recovery = history.latest_recovery('8.8.8.8')
```

### application/notifications.py

Multi-channel alert delivery (email, webhooks).

**Key Classes:**
- `EmailNotifier`: Send via SMTP
- `WebhookNotifier`: Send to Discord/Slack/generic
- `NotificationManager`: Coordinate notification delivery

**Supported Platforms:**
- Email (SMTP with TLS)
- Discord (embed messages)
- Slack (formatted blocks)
- Generic JSON webhooks

**Usage:**
```python
from application.notifications import NotificationManager, NotificationConfig

config = NotificationConfig.load('notification_config.json')
notif_mgr = NotificationManager(config)
notif_mgr.notify('8.8.8.8', 'High latency detected', 'warning')
```

### application/auth.py

User management and JWT authentication.

**Key Classes:**
- `User`: User account model
- `UserStore`: JSON file persistence
- `JWTTokenManager`: Token generation/validation
- `AuthenticationManager`: Login coordination

**Key Methods:**
- `AuthenticationManager.authenticate(username, password)`: Validate credentials
- `JWTTokenManager.create_token(username, role, expires_in_hours=24)`: Generate token
- `JWTTokenManager.verify_token(token)`: Validate token

**Usage:**
```python
from application.auth import AuthenticationManager

auth_mgr = AuthenticationManager('data/users.json')
token = auth_mgr.authenticate('admin', 'admin')
payload = auth_mgr.token_manager.verify_token(token)
```

### application/api.py

Production API utilities and decorators.

**Key Functions:**
- `api_response(data=None, error=None, status=200)`: Wrap responses
- `@validate_json(*required_fields)`: Validate request JSON
- `@rate_limit(max_requests=100, window_seconds=60)`: Rate limiting

**Response Format:**
```json
{
  "status": "success",
  "data": {
    ...
  }
}
```

**Usage:**
```python
from application.api import api_response, validate_json

@app.route('/api/example', methods=['POST'])
@validate_json('field1', 'field2')
def example():
    return api_response({'message': 'success'})
```

### application/dashboard.py

Flask web application and route definitions.

**Key Functions:**
- `create_app(config_path)`: Factory function
- `@require_token`: Authentication decorator

**Routes:**
- `GET /` - Serve dashboard HTML
- `GET /api/v1/health` - Health check
- `GET /api/v1/status` - System status
- `POST /api/auth/login` - User login
- `GET /api/history/<target>` - Target history

## Testing

### Running Tests

```bash
# Run all tests
python3 -m unittest discover -s tests -v

# Run specific test file
python3 -m unittest tests.test_latency_monitor -v

# Run with coverage
coverage run -m unittest discover -s tests
coverage report -m
coverage html  # Generate HTML report
```

### Writing Tests

Tests should follow these patterns:

```python
import unittest
from unittest.mock import patch, MagicMock
from tempfile import TemporaryDirectory

class MyTest(unittest.TestCase):
    def setUp(self):
        """Initialize before each test"""
        self.temp_dir = TemporaryDirectory()
    
    def tearDown(self):
        """Clean up after each test"""
        self.temp_dir.cleanup()
    
    def test_something(self):
        """Test description"""
        # Arrange
        expected = 'value'
        
        # Act
        result = some_function()
        
        # Assert
        self.assertEqual(result, expected)
    
    @patch('module.external_function')
    def test_with_mock(self, mock_func):
        """Test with mocked dependency"""
        mock_func.return_value = 'mocked'
        result = my_function()
        self.assertEqual(result, 'mocked')
```

### Test Fixtures

```python
# Use tempfile for database testing
from tempfile import NamedTemporaryFile

with NamedTemporaryFile(suffix='.db', delete=False) as f:
    store = MeasurementStore(f.name)
    # Test store operations
```

## Debugging

### Enable Debug Logging

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
logger.debug('Debug message')
```

### Using Python Debugger

```python
import pdb

# Set breakpoint in code
pdb.set_trace()

# Or in Python 3.7+
breakpoint()
```

### Common Issues

**Module import errors:**
```bash
# Ensure you're in project root
cd /Users/yohan/projects/latency-monitor

# Run with -m flag
python3 -m application.dashboard
```

**Database locked:**
```bash
# Remove WAL files
rm data/latency.db-wal data/latency.db-shm
```

**Port already in use:**
```bash
# Use different port
LATENCY_MONITOR_PORT=9000 python3 -m application.dashboard
```

## Performance

### Monitoring Performance

```bash
# Check memory usage
ps aux | grep application.dashboard

# Monitor with Docker
docker stats latency-monitor
```

### Optimization Tips

1. **Reduce ping frequency** for less critical targets
2. **Increase alert cooldown** to reduce redundant alerts
3. **Archive old measurements** to keep database size down
4. **Use connection pooling** for API clients

### Database Maintenance

```python
# Clean old measurements (older than 7 days)
from datetime import datetime, timedelta

cutoff = datetime.utcnow() - timedelta(days=7)
store.cursor.execute(
    'DELETE FROM measurements WHERE created_at < ?',
    (cutoff.isoformat(),)
)
store.connection.commit()
```

## Common Tasks

### Add New Target

**Configuration approach:**
```json
{
  "targets": ["8.8.8.8", "1.1.1.1", "9.9.9.9"]
}
```

**Programmatic approach:**
```python
from application.config import MonitorConfig

config = MonitorConfig.load('monitor_config.json')
config.targets.append('9.9.9.9')
config.save('monitor_config.json')
```

### Modify Alert Thresholds

```json
{
  "latency_threshold_ms": 150,
  "packet_loss_threshold": 5,
  "alert_cooldown_seconds": 600
}
```

### Add Custom Notification Channel

```python
# In application/notifications.py

class SlackNotifier:
    def send(self, message, severity):
        # Implementation
        pass

# Register in NotificationManager
if config.webhook.platform == 'slack':
    notifier = SlackNotifier(config.webhook.url)
```

### Create New API Endpoint

```python
# In application/dashboard.py

@app.route('/api/v1/custom', methods=['GET'])
@require_token
@rate_limit(max_requests=100, window_seconds=60)
def api_v1_custom():
    data = {...}
    return api_response(data)
```

## Code Style

**Follow PEP 8:**
- 4-space indentation
- Maximum line length: 120 characters
- Use meaningful names
- Add docstrings

**Example:**
```python
def calculate_packet_loss(failed_count: int, total_count: int) -> float:
    """
    Calculate packet loss percentage.
    
    Args:
        failed_count: Number of failed pings
        total_count: Total number of pings
    
    Returns:
        Packet loss percentage (0-100)
    
    Example:
        >>> calculate_packet_loss(1, 10)
        10.0
    """
    if total_count == 0:
        return 0.0
    return (failed_count / total_count) * 100
```

## Version Control

**Commit Message Format:**
```
[TYPE] Brief description

Detailed explanation (optional)

Fixes #123
```

**Types:**
- `feature`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `test`: Test changes
- `refactor`: Code refactoring
- `perf`: Performance improvements

## Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Python subprocess](https://docs.python.org/3/library/subprocess.html)
- [SQLite3](https://docs.python.org/3/library/sqlite3.html)
- [PEP 8 Style Guide](https://pep8.org/)
- [Git Workflow](https://github.com/yohan-sys-prog/latency-monitor/contributing)

## Support

For development questions:
1. Check existing documentation
2. Review code comments
3. Look at similar modules
4. Ask in GitHub Discussions
5. Create an issue with [help wanted] tag
