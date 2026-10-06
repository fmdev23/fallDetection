"""Run: python -m unittest discover -s test -v"""
import math
import unittest
from python_app.sensor_analyzer import analyze_sensor
from python_app.sensor_reader import parse_sensor_line


class SensorTests(unittest.TestCase):
    def test_normal_and_each_impact_source(self):
        self.assertEqual(analyze_sensor((0, 0, 1, 0, 0, 0)).status, "NORMAL")
        self.assertEqual(analyze_sensor((0, 0, 2.1, 0, 0, 0)).status, "IMPACT")
        self.assertEqual(analyze_sensor((0, 0, 1, 151, 0, 0)).status, "IMPACT")
        self.assertEqual(analyze_sensor((0, 0, 2, 150, 0, 0)).status, "NORMAL")

    def test_norms_and_configurable_threshold(self):
        result = analyze_sensor((3, 4, 0, 0, 5, 12), 6, 14)
        self.assertEqual((result.accel_total, result.gyro_total), (5, 13))
        self.assertEqual(result.status, "NORMAL")

    def test_packets(self):
        self.assertEqual(parse_sensor_line(b'SENSOR,0,0,1,0,0,0\r\n'),
                         (0, 0, 1, 0, 0, 0))
        for line in ("boot", "SENSOR,1,2", "SENSOR,x,0,1,0,0,0",
                     "SENSOR,nan,0,1,0,0,0", "SENSOR,inf,0,1,0,0,0"):
            with self.subTest(line=line):
                self.assertIsNone(parse_sensor_line(line))

    def test_reject_invalid_values_and_thresholds(self):
        for values in ((1, 2), (math.nan, 0, 1, 0, 0, 0)):
            with self.assertRaises(ValueError):
                analyze_sensor(values)
        for threshold in (0, -1, math.nan, math.inf):
            with self.assertRaises(ValueError):
                analyze_sensor((0,) * 6, threshold)


if __name__ == "__main__":
    unittest.main()
