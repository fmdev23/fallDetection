import csv
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from python_app.main import EventLogger


class EventTests(unittest.TestCase):
    def test_only_important_changes_and_append(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / "results" / "events.csv"
            logger = EventLogger(path)
            logger.record("UPRIGHT", "NORMAL", "NORMAL")
            for _ in range(100):
                self.assertFalse(logger.record("UPRIGHT", "NORMAL", "NORMAL"))
            logger.record("LYING", "NORMAL", "SUSPICIOUS")
            logger.record("LYING", "IMPACT", "SUSPICIOUS")
            logger.record("LYING", "NORMAL", "FALL_DETECTED")
            logger.record("UNKNOWN", "SENSOR_DISCONNECTED", "FALL_DETECTED")
            EventLogger(path).record("UPRIGHT", "NORMAL", "NORMAL")
            with path.open(encoding="utf-8") as source:
                rows = list(csv.DictReader(source))
            self.assertEqual(len(rows), 5)
            self.assertEqual(rows[2]["final_status"], "FALL_DETECTED")
            self.assertTrue(all(row["timestamp"].endswith("+00:00") for row in rows))


if __name__ == "__main__":
    unittest.main()
