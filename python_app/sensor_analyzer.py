"""Experimental thresholds for the course prototype, not medical thresholds."""

from dataclasses import dataclass
import math

ACCEL_THRESHOLD = 2.0  # g
GYRO_THRESHOLD = 150.0  # deg/s


class MotionRisk:
    """Experimental early warning, independent of pose and impact confirmation.

    Moderate excursions need two samples spanning 80 ms; impact and a sharp
    acceleration change warn immediately. Rearm after 1 s of quiet readings.
    """
    def __init__(self):
        self.previous = None
        self.since = self.last_risk = None
        self.latched = False
        self.reason = ""

    def update(self, values, now, impact=False):
        accel, gyro = math.hypot(*values[:3]), math.hypot(*values[3:])
        jerk = 0.0
        if self.previous is not None:
            before, timestamp = self.previous
            dt = now - timestamp
            if .005 <= dt <= .25:
                jerk = math.dist(values[:3], before) / dt
            elif dt > .25:
                self.since = None
        self.previous = (tuple(values[:3]), now)
        abrupt = jerk >= 5 and (abs(accel-1) >= .25 or gyro >= 60)
        candidate = impact or accel >= 1.6 or accel <= .55 or gyro >= 100 or abrupt
        event = False
        if candidate:
            if self.since is None:
                self.since = now
            if impact or abrupt or now-self.since >= .08-1e-9:
                event = not self.latched
                self.latched = True
                self.last_risk = now
                self.reason = (f"Chuyển động bất thường: {accel:.2f} g, {gyro:.0f} °/s, "
                               f"biến thiên {jerk:.1f} g/s. Cần kiểm tra ngay; chưa xác nhận té.")
        else:
            self.since = None
            if self.last_risk is not None and now-self.last_risk >= 1:
                self.latched = False
        active = self.last_risk is not None and now-self.last_risk < 1
        return active, event, self.reason, jerk


@dataclass(frozen=True)
class SensorAnalysis:
    accel_total: float
    gyro_total: float
    status: str


def analyze_sensor(values, accel_threshold=ACCEL_THRESHOLD,
                   gyro_threshold=GYRO_THRESHOLD):
    """Accept ax, ay, az in g; gx, gy, gz in deg/s."""
    if len(values) != 6 or not all(math.isfinite(v) for v in values):
        raise ValueError("Sensor requires six finite numbers")
    if not all(math.isfinite(t) and t > 0 for t in
               (accel_threshold, gyro_threshold)):
        raise ValueError("Thresholds must be finite and positive")
    accel_total = math.hypot(*values[:3])
    gyro_total = math.hypot(*values[3:])
    status = ("IMPACT" if accel_total > accel_threshold or
              gyro_total > gyro_threshold else "NORMAL")
    return SensorAnalysis(accel_total, gyro_total, status)
