# Architecture

This project follows a staged architecture for a production-ready monitoring system.

## Components

- `application/monitor.py`: multi-target ping execution and aggregation
- `application/storage.py`: SQLite persistence layer for measurements and incidents
- `application/alerts.py`: alert evaluation and cooldown logic
- `application/history.py`: historical queries for averages and incidents
- `application/dashboard.py`: Flask dashboard and status endpoints
- `application/config.py`: persistent runtime settings

## Runtime flow

1. The config file is loaded from `monitor_config.json`.
2. The monitor loop pings each configured target.
3. Results are stored in SQLite and aggregated in memory.
4. The dashboard exposes JSON endpoints for live status and historical reads.
5. Alert rules evaluate latency and packet loss thresholds and register incidents.

## Deployment

The application is containerizable and can be run via Docker Compose.
