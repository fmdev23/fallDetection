"""Read the existing Wokwi SENSOR protocol without changing firmware."""
import argparse
import math
import time
import threading
from dataclasses import dataclass
import serial

if __package__:
    from .sensor_analyzer import ACCEL_THRESHOLD, GYRO_THRESHOLD, analyze_sensor, MotionRisk
else:
    from sensor_analyzer import ACCEL_THRESHOLD, GYRO_THRESHOLD, analyze_sensor, MotionRisk

PORT = "rfc2217://localhost:4000"


@dataclass(frozen=True)
class SensorSnapshot:
    status: str = "SENSOR_DISCONNECTED"
    accel_total: float | None = None
    gyro_total: float | None = None
    timestamp: float | None = None
    impact_at: float | None = None
    risk_active: bool = False
    risk_event: bool = False
    risk_reason: str = ""
    jerk: float = 0.0


class SensorStream:
    """One serial owner; camera never waits for the network/serial read."""
    def __init__(self, port=PORT, accel_threshold=ACCEL_THRESHOLD,
                 gyro_threshold=GYRO_THRESHOLD, stale_after=.75, on_sample=None):
        analyze_sensor((0,) * 6, accel_threshold, gyro_threshold)
        self.port = port
        self.accel_threshold = accel_threshold
        self.gyro_threshold = gyro_threshold
        self.stale_after = stale_after
        self.on_sample = on_sample
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._sample = SensorSnapshot()
        self._thread = threading.Thread(target=self._run, daemon=True, name="wokwi-reader")

    def start(self):
        self._thread.start()
        return self

    def snapshot(self, now=None):
        now = time.monotonic() if now is None else now
        with self._lock:
            sample = self._sample
        if sample.timestamp is None or now - sample.timestamp > self.stale_after:
            return SensorSnapshot()
        return sample

    def _publish(self, sample):
        with self._lock:
            self._sample = sample
        if self.on_sample is not None:
            self.on_sample(sample)

    def _run(self):
        while not self._stop.is_set():
            try:
                with serial.serial_for_url(self.port, baudrate=115200, timeout=.25) as ser:
                    ser.reset_input_buffer()
                    previous_status = None
                    impact_at = None
                    last_valid = time.monotonic()
                    risk = MotionRisk()
                    while not self._stop.is_set():
                        values = parse_sensor_line(ser.read_until(b"\n", size=256))
                        now = time.monotonic()
                        if values is None:
                            if now - last_valid > self.stale_after:
                                self._publish(SensorSnapshot())
                                previous_status = impact_at = None
                                risk = MotionRisk()
                            continue
                        result = analyze_sensor(values, self.accel_threshold, self.gyro_threshold)
                        if result.status == "IMPACT" and previous_status != "IMPACT":
                            impact_at = now
                        previous_status, last_valid = result.status, now
                        active, event, reason, jerk = risk.update(values, now, result.status == "IMPACT")
                        self._publish(SensorSnapshot(result.status, result.accel_total,
                                                     result.gyro_total, now, impact_at,
                                                     active, event, reason, jerk))
            except (serial.SerialException, OSError):
                self._publish(SensorSnapshot())
                self._stop.wait(1)

    def close(self):
        self._stop.set()
        self._thread.join(timeout=6)


def parse_sensor_line(line):
    """Ignore startup messages, truncated packets and invalid numbers."""
    if isinstance(line, bytes):
        line = line.decode("utf-8", errors="replace")
    parts = line.strip().split(",")
    if len(parts) != 7 or parts[0] != "SENSOR":
        return None
    try:
        values = tuple(float(value) for value in parts[1:])
    except ValueError:
        return None
    return values if all(math.isfinite(value) for value in values) else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", default=PORT)
    parser.add_argument("--accel-threshold", type=float, default=ACCEL_THRESHOLD)
    parser.add_argument("--gyro-threshold", type=float, default=GYRO_THRESHOLD)
    parser.add_argument("--duration", type=float, default=0,
                        help="Stop after N seconds; 0 means until Ctrl+C")
    args = parser.parse_args()
    try:
        analyze_sensor((0,) * 6, args.accel_threshold, args.gyro_threshold)
        if not math.isfinite(args.duration) or args.duration < 0:
            raise ValueError("Duration must be finite and nonnegative")
    except ValueError as exc:
        parser.error(str(exc))
    start = time.monotonic()
    last_print = -math.inf
    last_status = None
    last_valid = start
    print("Dang ket noi voi MPU6050 tren Wokwi...", flush=True)
    try:
        with serial.serial_for_url(args.port, baudrate=115200, timeout=0.5) as ser:
            print("Da ket noi! Nhan Ctrl+C de dung.", flush=True)
            while not args.duration or time.monotonic() - start < args.duration:
                values = parse_sensor_line(ser.readline())
                now = time.monotonic()
                if values is None:
                    if now - last_valid >= 2 and last_status != "SENSOR_DISCONNECTED":
                        print("SENSOR_DISCONNECTED: khong nhan du lieu hop le.", flush=True)
                        last_status = "SENSOR_DISCONNECTED"
                    continue
                last_valid = now
                result = analyze_sensor(values, args.accel_threshold, args.gyro_threshold)
                if result.status != last_status or now - last_print >= 1:
                    print(f"Accel Total: {result.accel_total:.2f} g | "
                          f"Gyro Total: {result.gyro_total:.2f} deg/s | "
                          f"Status: {result.status}", flush=True)
                    last_print, last_status = now, result.status
    except KeyboardInterrupt:
        print("\nDung chuong trinh.")
    except (serial.SerialException, OSError) as exc:
        print(f"SENSOR_DISCONNECTED: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
