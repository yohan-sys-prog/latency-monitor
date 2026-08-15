# latency-monitor

A lightweight multi-target network monitoring app that tracks ping latency, failure counts, alerts, and basic historical trends.

## Features

- multi-target ping monitoring
- current, min, max, and average latency tracking
- failed ping counting
- SQLite-backed persistence for measurements and incidents
- live Flask dashboard
- CLI monitoring mode
- configurable thresholds and targets

## Quick start

Run the dashboard locally:

```bash
cd /Users/yohan/projects/latency-monitor
python3 -m application.dashboard
```

Then open:

```text
http://localhost:8000
```

Run the CLI monitor:

```bash
cd /Users/yohan/projects/latency-monitor
python3 -m application.cli --targets 8.8.8.8 1.1.1.1 --interval 1.0 --iterations 5
```

## Configuration

The default settings live in `monitor_config.json` and include:

- monitored targets
- ping interval
- latency thresholds
- packet-loss thresholds
- dashboard host and port
- SQLite database path

## Docker

```bash
docker compose up
```

## Notes

This project is built as a practical monitoring foundation that can continue advancing toward a fuller network operations dashboard, alerting system, and deployment-ready application stack.
