# Configuration Examples

This directory contains example configuration files for different deployment scenarios and notification setups.

## Monitor Configuration Examples

### Basic Setup (`monitor_config_basic.json`)

For small deployments monitoring 2 public DNS servers:

```bash
cp examples/monitor_config_basic.json monitor_config.json
# Or use as-is since it's the default
```

**Best for:**
- Personal use
- Testing/development
- Simple home lab setups

### Enterprise Setup (`monitor_config_enterprise.json`)

For larger deployments monitoring multiple critical services:

```bash
cp examples/monitor_config_enterprise.json monitor_config.json
python3 -m application.dashboard
```

**Best for:**
- Production deployments
- Multi-service monitoring
- Corporate networks

**Features:**
- 6+ monitored targets
- Tighter latency thresholds (150ms)
- Longer alert cooldown (600s)
- Stricter packet loss tolerance (5%)

## Notification Configuration Examples

### Email Alerts (`notification_config_email.json`)

Set up email notifications via SMTP:

```bash
cp examples/notification_config_email.json notification_config.json
# Edit the file with your email credentials
```

**Configuration steps:**

1. **Gmail:**
   ```bash
   # Set sender_email to your Gmail address
   # Generate app password: https://myaccount.google.com/apppasswords
   # Set password to the generated app password (16 characters)
   ```

2. **Office 365:**
   ```json
   {
     "email": {
       "enabled": true,
       "smtp_host": "smtp.office365.com",
       "smtp_port": 587,
       "use_tls": true,
       "sender_email": "your-email@company.com",
       "password": "your-password"
     }
   }
   ```

3. **Self-hosted Postfix/Sendmail:**
   ```json
   {
     "email": {
       "enabled": true,
       "smtp_host": "localhost",
       "smtp_port": 25,
       "use_tls": false,
       "sender_email": "monitoring@example.com"
     }
   }
   ```

### Discord Webhook (`notification_config_discord.json`)

Set up alerts to Discord channel:

```bash
cp examples/notification_config_discord.json notification_config.json
# Edit with your Discord webhook URL
```

**Getting a Discord Webhook URL:**

1. Open your Discord server
2. Go to channel settings → Integrations → Webhooks
3. Click "New Webhook"
4. Copy the webhook URL
5. Paste into `notification_config.json`

### Slack Webhook (`notification_config_slack.json`)

Set up alerts to Slack channel:

```bash
cp examples/notification_config_slack.json notification_config.json
# Edit with your Slack webhook URL
```

**Getting a Slack Webhook URL:**

1. Go to https://api.slack.com/apps
2. Create a new app or select existing
3. Enable "Incoming Webhooks"
4. Click "Add New Webhook to Workspace"
5. Select channel and authorize
6. Copy the webhook URL
7. Paste into `notification_config.json`

## Multi-Channel Notifications

Combine email and webhook notifications:

```json
{
  "email": {
    "enabled": true,
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587,
    "use_tls": true,
    "sender_email": "your-email@gmail.com",
    "password": "your-app-password",
    "recipient_emails": ["alerts@example.com"]
  },
  "webhook": {
    "enabled": true,
    "url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
    "platform": "slack"
  }
}
```

## Docker Deployment Configuration

### Using Example Configs with Docker Compose

```bash
# Copy your chosen configuration
cp examples/monitor_config_enterprise.json monitor_config.json
cp examples/notification_config_slack.json notification_config.json

# Start the container
docker compose up -d

# View logs
docker logs -f latency-monitor
```

### Environment Overrides

In your `compose.yaml`:

```yaml
environment:
  LATENCY_MONITOR_PORT: "9000"
  LATENCY_MONITOR_HOST: "0.0.0.0"
  NOTIFICATION_EMAIL_ENABLED: "true"
  NOTIFICATION_WEBHOOK_ENABLED: "true"
```

## Testing Notifications

After configuring notifications, test them:

```bash
# Start the application with verbose output
python3 -m application.dashboard

# In another terminal, trigger an alert by pinging an unreachable host
# Modify monitor_config.json to include: "192.0.2.1" (TEST-NET-1, always unreachable)

# Check logs for notification delivery
```

## Customization

### Custom SMTP Server

For any SMTP server, configure:

```json
{
  "email": {
    "enabled": true,
    "smtp_host": "mail.example.com",
    "smtp_port": 587,
    "use_tls": true,
    "sender_email": "alerts@example.com",
    "password": "secure-password",
    "recipient_emails": ["ops@example.com", "admin@example.com"]
  }
}
```

### Generic Webhook

For any webhook endpoint:

```json
{
  "webhook": {
    "enabled": true,
    "url": "https://your-service.com/webhooks/alerts",
    "platform": "generic"
  }
}
```

The generic platform sends:
```json
{
  "target": "8.8.8.8",
  "message": "High latency detected",
  "severity": "warning",
  "timestamp": "2024-08-15T10:30:45.123456Z"
}
```

## Troubleshooting

### Email Not Being Sent

1. **Check SMTP credentials**
   ```bash
   python3 -c "
   import smtplib
   try:
       s = smtplib.SMTP('smtp.gmail.com', 587)
       s.starttls()
       s.login('your-email@gmail.com', 'your-app-password')
       print('✓ SMTP login successful')
       s.quit()
   except Exception as e:
       print(f'✗ SMTP error: {e}')
   "
   ```

2. **Check firewall**
   - Ensure port 587 (SMTP) is not blocked
   - Try telnet: `telnet smtp.gmail.com 587`

3. **Check logs**
   ```bash
   docker logs latency-monitor | grep -i email
   # or
   tail -f application.log | grep -i email
   ```

### Webhook Not Triggering

1. **Verify webhook URL**
   ```bash
   curl -X POST https://hooks.slack.com/services/YOUR/WEBHOOK/URL \
     -H "Content-Type: application/json" \
     -d '{"text":"Test message"}'
   ```

2. **Check firewall**
   - Ensure outbound HTTPS (port 443) is allowed

3. **View application logs**
   ```bash
   docker logs latency-monitor | grep -i webhook
   ```

## Security Notes

- **Never commit secrets** to git (use .gitignore)
- **Rotate credentials** regularly
- Use **app-specific passwords** for email (Gmail, Office 365)
- Keep webhook URLs **secret** (don't share in public repos)
- Use **HTTPS** for all webhook endpoints

## Support

For issues with specific services:

- **Gmail**: https://support.google.com/accounts/answer/185833
- **Office 365**: https://docs.microsoft.com/office365/
- **Slack**: https://api.slack.com/messaging/webhooks
- **Discord**: https://discord.com/developers/docs/resources/webhook

See the main README.md for general troubleshooting and support options.
