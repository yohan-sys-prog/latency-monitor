import argparse
import sys
from pathlib import Path

from application.config import load_config
from application.monitor import PingMonitor
from application.storage import MeasurementStore


def main() -> int:
    parser = argparse.ArgumentParser(description="Monitor internet latency across multiple targets.")
    parser.add_argument("--config", default="monitor_config.json", help="Path to config json file.")
    parser.add_argument("--targets", nargs="*", default=None, help="Targets to monitor.")
    parser.add_argument("--interval", type=float, default=None, help="Seconds between each ping cycle.")
    parser.add_argument("--iterations", type=int, default=0, help="Iterations to run before exit. 0 means forever.")
    args = parser.parse_args()

    config = load_config(args.config)
    if args.targets:
        config.targets = args.targets
    if args.interval is not None:
        config.interval = args.interval

    store = MeasurementStore(config.db_path)
    monitor = PingMonitor(config.targets, interval=config.interval, store=store)

    attempt = 0
    try:
        while args.iterations == 0 or attempt < args.iterations:
            attempt += 1
            snapshot = monitor.run_once()
            for target, stats in snapshot.items():
                current = stats["current"]
                avg = stats["avg"]
                minimum = stats["min"]
                maximum = stats["max"]
                failed = stats["failed"]
                if current is None:
                    print(f"{target}: FAIL | Min={minimum} | Max={maximum} | Avg={avg} | Failed={failed}")
                else:
                    print(f"{target}: {current:.2f} ms | Avg={avg:.2f} ms | Min={minimum:.2f} ms | Max={maximum:.2f} ms | Failed={failed}")
            if args.iterations != 0 and attempt >= args.iterations:
                break
            import time
            time.sleep(config.interval)
        return 0
    except KeyboardInterrupt:
        print("\nStopping monitor.")
        return 0
    except Exception as exc:  # pragma: no cover
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
