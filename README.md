# latency-monitor

A lightweight multi-target latency and network monitor for macOS/Linux.

## Features

- multi-target ping monitoring
- min, max, and average latency tracking
- failed ping counting
- SQLite-backed persistence for history and incidents
- optional Flask dashboard
- command-line monitoring mode

## Quick start

```bash
python3 -m application.cli --targets 8.8.8.8 1.1.1.1 --interval 1.0 --iterations 5
```

```bash
python3 -m application.dashboard
```

Then open: http://localhost:8000

## Configuration

The default config is saved to `monitor_config.json`.

## Notes

This project is intentionally built in stages so it can evolve toward a fuller network monitoring system while staying stable and testable.
