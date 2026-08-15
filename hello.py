import argparse
import re
import statistics
import subprocess
import sys
import time


def run_ping(target: str) -> float | None:
    """Return a ping time in milliseconds, or None if the request failed."""
    try:
        completed = subprocess.run(
            ["ping", "-c", "1", "-W", "1000", target],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (FileNotFoundError, OSError):
        raise RuntimeError("The 'ping' command is not available on this system.")

    output = (completed.stdout or "") + "\n" + (completed.stderr or "")
    match = re.search(r"time=(\d+(?:\.\d+)?)\s*ms", output, re.IGNORECASE)
    if match:
        return float(match.group(1))

    if any(
        marker in output.lower()
        for marker in (
            "100.0% packet loss",
            "request timeout",
            "no answer yet",
            "destination host unreachable",
            "100% packet loss",
        )
    ):
        return None

    return None


def format_stat(value: float | None) -> str:
    return "N/A" if value is None else f"{value:.2f} ms"


def main() -> int:
    parser = argparse.ArgumentParser(description="Monitor internet latency continuously.")
    parser.add_argument(
        "target",
        nargs="?",
        default="8.8.8.8",
        help="IP address or hostname to ping.",
    )
    parser.add_argument(
        "--target",
        dest="target_flag",
        default=None,
        help="IP address or hostname to ping.",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help="Seconds between pings (default: 1.0)",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=0,
        help="Number of pings to attempt before exiting. 0 means run forever.",
    )
    args = parser.parse_args()
    if args.target_flag is not None:
        args.target = args.target_flag

    samples: list[float] = []
    failed = 0
    current: float | None = None
    minimum: float | None = None
    maximum: float | None = None
    average: float | None = None

    print(f"Monitoring {args.target} every {args.interval:.1f}s (Ctrl+C to stop).")

    attempt = 0
    try:
        while args.iterations == 0 or attempt < args.iterations:
            attempt += 1
            current = run_ping(args.target)

            if current is None:
                failed += 1
                print(
                    f"\rCurrent: FAIL | Min: {format_stat(minimum)} | "
                    f"Max: {format_stat(maximum)} | Avg: {format_stat(average)} | "
                    f"Failed: {failed}",
                    end="",
                    flush=True,
                )
            else:
                samples.append(current)
                minimum = min(samples)
                maximum = max(samples)
                average = statistics.fmean(samples)
                print(
                    f"\rCurrent: {current:.2f} ms | Min: {minimum:.2f} ms | "
                    f"Max: {maximum:.2f} ms | Avg: {average:.2f} ms | Failed: {failed}",
                    end="",
                    flush=True,
                )

            if args.iterations != 0 and attempt >= args.iterations:
                break
            time.sleep(args.interval)

        print("\n")
        return 0
    except KeyboardInterrupt:
        print("\nStopping ping monitor.")
        return 0
    except RuntimeError as exc:
        print(f"\nError: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
