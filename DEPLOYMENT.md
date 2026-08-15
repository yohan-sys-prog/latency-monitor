# Deployment Guide

This guide covers deploying the latency-monitor application in various environments.

## Table of Contents

1. [Local Development](#local-development)
2. [Docker Deployment](#docker-deployment)
3. [Linux Server](#linux-server)
4. [Cloud Platforms](#cloud-platforms)
5. [Production Hardening](#production-hardening)

## Local Development

### Prerequisites

- Python 3.10+
- pip package manager

### Setup

```bash
# Clone repository
git clone https://github.com/yohan-sys-prog/latency-monitor.git
cd latency-monitor

# Install dependencies
pip install -r requirements.txt

# Run dashboard
python3 -m application.dashboard

# Access at http://localhost:8000
```

### Configuration

Edit `monitor_config.json`:

```json
{
  "targets": ["8.8.8.8", "1.1.1.1"],
  "interval": 2.0,
  "latency_threshold_ms": 100,
  "packet_loss_threshold": 10,
  "alert_cooldown_seconds": 300,
  "dashboard_port": 8000
}
```

## Docker Deployment

### Quick Start

```bash
docker compose up
```

Access at http://localhost:8000

### Production Docker Setup

```bash
# Build image
docker build -t latency-monitor:latest .

# Run container
docker run -d \
  --name latency-monitor \
  -p 8000:8000 \
  -v latency-data:/app/data \
  -v $(pwd)/monitor_config.json:/app/monitor_config.json:ro \
  --restart unless-stopped \
  latency-monitor:latest
```

### Docker Environment Variables

- `LATENCY_MONITOR_PORT`: Dashboard port (default: 8000)
- `LATENCY_MONITOR_HOST`: Bind address (default: 0.0.0.0)
- `PYTHONUNBUFFERED`: Set to 1

### Health Checks

The Docker image includes health checks:

```bash
docker ps  # View health status
docker logs latency-monitor  # View logs
```

## Linux Server

### Systemd Service

Create `/etc/systemd/system/latency-monitor.service`:

```ini
[Unit]
Description=Latency Monitor
After=network.target

[Service]
Type=simple
User=latency-monitor
WorkingDirectory=/opt/latency-monitor
ExecStart=/usr/bin/python3 -m application.dashboard
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Installation

```bash
# Create user
sudo useradd -r -s /bin/false latency-monitor

# Install application
sudo mkdir -p /opt/latency-monitor
cd /opt/latency-monitor
sudo git clone https://github.com/yohan-sys-prog/latency-monitor.git .
sudo pip install -r requirements.txt

# Enable service
sudo systemctl daemon-reload
sudo systemctl enable latency-monitor
sudo systemctl start latency-monitor

# Check status
sudo systemctl status latency-monitor
```

### Nginx Reverse Proxy

```nginx
upstream latency_monitor {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name monitor.example.com;

    location / {
        proxy_pass http://latency_monitor;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/ {
        proxy_pass http://latency_monitor;
        proxy_set_header Authorization $http_authorization;
    }
}
```

### Enable HTTPS with Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d monitor.example.com
```

## Cloud Platforms

### AWS EC2

```bash
# Launch Ubuntu 22.04 instance
# Install Docker
sudo apt update && sudo apt install -y docker.io docker-compose

# Clone and run
git clone https://github.com/yohan-sys-prog/latency-monitor.git
cd latency-monitor
docker compose up -d
```

### Heroku

```bash
# Install Heroku CLI
# Create app
heroku create your-latency-monitor

# Deploy
git push heroku main

# View logs
heroku logs --tail
```

### DigitalOcean App Platform

```bash
# Create app.yaml
name: latency-monitor
services:
- name: monitor
  github:
    branch: main
    repo: your-username/latency-monitor
  build_command: pip install -r requirements.txt
  run_command: python3 -m application.dashboard
  http_port: 8000
  envs:
  - key: LATENCY_MONITOR_PORT
    value: "8000"
```

## Production Hardening

### Security Best Practices

1. **Change Default Credentials**
   ```bash
   # After first login, change password
   curl -X POST http://localhost:8000/api/auth/change-password \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -d '{"new_password": "secure_password"}'
   ```

2. **Enable Notifications**
   - Configure email alerts in `notification_config.json`
   - Set up Discord/Slack webhooks
   - Test notification delivery

3. **Use HTTPS**
   - Deploy behind reverse proxy (Nginx/Caddy)
   - Use Let's Encrypt certificates
   - Set secure headers

4. **Database Backups**
   ```bash
   # Backup SQLite database
   cp data/latency.db backups/latency_$(date +%Y%m%d).db
   ```

5. **Monitor Logs**
   ```bash
   # Check application logs
   tail -f /var/log/latency-monitor.log
   
   # Monitor system resources
   docker stats latency-monitor
   ```

### Resource Limits

For Docker:

```yaml
deploy:
  resources:
    limits:
      cpus: '1.0'
      memory: 512M
    reservations:
      cpus: '0.5'
      memory: 256M
```

### Log Rotation

```bash
# Configure logrotate (Linux)
/var/log/latency-monitor.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    create 0640 latency-monitor latency-monitor
    sharedscripts
    postrotate
        systemctl reload latency-monitor > /dev/null 2>&1 || true
    endscript
}
```

### Monitoring & Alerts

Configure notification settings to receive alerts:

```json
{
  "email": {
    "enabled": true,
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "alerts@example.com",
    "recipient_emails": ["ops@example.com"]
  },
  "webhook": {
    "enabled": true,
    "url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
    "platform": "slack"
  }
}
```

## Troubleshooting

### Port Already in Use

```bash
# Change port in monitor_config.json
LATENCY_MONITOR_PORT=9000 python3 -m application.dashboard
```

### Database Lock

```bash
# Remove stale database lock
rm data/latency.db-wal data/latency.db-shm
```

### Authentication Issues

```bash
# Reset to default credentials
rm data/users.json

# Restart application (will create admin/admin user)
systemctl restart latency-monitor
```

### High Memory Usage

```bash
# Reduce sample retention in storage.py
# Increase alert_cooldown_seconds in monitor_config.json
# Deploy with memory limits
```

## Support

For issues and feature requests, visit:
https://github.com/yohan-sys-prog/latency-monitor/issues
