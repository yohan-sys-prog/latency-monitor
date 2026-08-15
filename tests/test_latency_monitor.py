import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from application.alerts import AlertManager
from application.config import MonitorConfig
from application.history import HistoryQuery
from application.monitor import PingMonitor
from application.storage import MeasurementStore


class PingMonitorTests(unittest.TestCase):
    def test_multiple_targets_have_separate_stats(self):
        monitor = PingMonitor(targets=["8.8.8.8", "1.1.1.1"])
        self.assertEqual(len(monitor.targets), 2)
        self.assertEqual(monitor.targets[0], "8.8.8.8")
        self.assertEqual(monitor.targets[1], "1.1.1.1")

    def test_store_persists_measurements(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "latency.db"
            store = MeasurementStore(db_path)
            store.record_measurement("8.8.8.8", 14.5)
            store.record_measurement("8.8.8.8", 21.0)

            with sqlite3.connect(db_path) as conn:
                count = conn.execute("SELECT COUNT(*) FROM measurements WHERE target = ?", ("8.8.8.8",)).fetchone()[0]
                self.assertEqual(count, 2)

    def test_alert_manager_registers_incident(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "latency.db"
            store = MeasurementStore(db_path)
            manager = AlertManager(store)
            alert = manager.evaluate("8.8.8.8", {"current": 250.0, "packet_loss_percent": 0.0}, 200.0, 10.0)
            self.assertIsNotNone(alert)
            self.assertEqual(alert["target"], "8.8.8.8")
            self.assertIn("High latency", alert["message"])

    def test_packet_loss_percent_tracks_failures(self):
        monitor = PingMonitor(targets=["8.8.8.8"])
        with patch.object(PingMonitor, "_ping_once", side_effect=[None, 42.5]):
            first = monitor.run_once()
            second = monitor.run_once()

        self.assertEqual(first["8.8.8.8"]["packet_loss_percent"], 100.0)
        self.assertEqual(second["8.8.8.8"]["packet_loss_percent"], 50.0)

    def test_recovery_detection_logic(self):
        """Test that recovery is detected after an outage."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "latency.db"
            store = MeasurementStore(db_path)
            history = HistoryQuery(store)
            
            # Record a failure incident
            store.record_incident("8.8.8.8", "Connection lost", severity="critical")
            
            # Record a successful measurement after the incident
            import time
            time.sleep(0.01)
            store.record_measurement("8.8.8.8", 42.5, success=True)
            
            recovery = history.latest_recovery("8.8.8.8")
            self.assertIsNotNone(recovery)
            self.assertIsNotNone(recovery["recovered_at"])

    def test_config_defaults_are_loaded(self):
        config = MonitorConfig()
        self.assertIn("8.8.8.8", config.targets)
        self.assertEqual(config.dashboard_port, 8000)


if __name__ == "__main__":
    unittest.main()
