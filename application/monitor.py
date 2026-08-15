import re
import statistics
import subprocess


class PingMonitor:
    def __init__(self, targets, interval=1.0, store=None):
        self.targets = list(targets)
        self.interval = float(interval)
        self.store = store
        self.history = {target: [] for target in self.targets}
        self.failures = {target: 0 for target in self.targets}
        self.current = {target: None for target in self.targets}

    def _ping_once(self, target: str) -> float | None:
        try:
            completed = subprocess.run(
                ["ping", "-c", "1", "-W", "1000", target],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
        except (FileNotFoundError, OSError) as exc:  # pragma: no cover - environment-specific
            raise RuntimeError("The 'ping' command is not available on this system.") from exc

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

    def run_once(self):
        results = {}
        for target in self.targets:
            value = self._ping_once(target)
            self.current[target] = value

            if value is None:
                self.failures[target] += 1
                if self.store is not None:
                    self.store.record_measurement(target, None, success=False)
                history = self.history[target]
                results[target] = {
                    "current": None,
                    "min": min(history) if history else None,
                    "max": max(history) if history else None,
                    "avg": statistics.fmean(history) if history else None,
                    "failed": self.failures[target],
                }
                continue

            self.history[target].append(value)
            if self.store is not None:
                self.store.record_measurement(target, value, success=True)

            history = self.history[target]
            results[target] = {
                "current": value,
                "min": min(history),
                "max": max(history),
                "avg": statistics.fmean(history),
                "failed": self.failures[target],
            }

        return results
