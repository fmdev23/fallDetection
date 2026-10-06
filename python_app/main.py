"""Shared camera/video fall warnings with conservative single-person IMU binding."""

import argparse
import csv
from dataclasses import dataclass
from datetime import datetime, timezone
import math
import queue
from pathlib import Path
import sys
import threading
import time

if __package__:
    from .alerts import AlertNotifier
    from .pose_detector import PoseDetector, open_capture
    from .posture_analyzer import posture_from_result
    from .sensor_reader import SensorStream, SensorSnapshot, PORT
    from .scene_analyzer import SceneAnalyzer
else:
    from alerts import AlertNotifier
    from pose_detector import PoseDetector, open_capture
    from posture_analyzer import posture_from_result
    from sensor_reader import SensorStream, SensorSnapshot, PORT
    from scene_analyzer import SceneAnalyzer


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=("webcam", "video", "image"), default="webcam")
    parser.add_argument("--path", help="Video/image file path")
    parser.add_argument("--video-live-sensor", action="store_true",
                        help="Explicit realtime video + live IMU demo; default video analyzes every frame without IMU")
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--port", default=PORT)
    parser.add_argument("--accel-threshold", type=float, default=2.0)
    parser.add_argument("--gyro-threshold", type=float, default=150.0)
    parser.add_argument("--impact-window", type=float, default=5.0)
    parser.add_argument("--lying-hold", type=float, default=1.3)
    parser.add_argument("--recovery-hold", type=float, default=2.0)
    parser.add_argument("--occlusion-grace", type=float, default=.6)
    parser.add_argument("--lying-warning", type=float, default=1.3)
    parser.add_argument("--no-alerts", action="store_true", help="Disable sound/popups for unattended tests")
    parser.add_argument("--duration", type=float, default=0,
                        help="Optional duration in seconds, 0 = until q")
    parser.add_argument("--log", type=Path,
                        default=Path(__file__).resolve().parents[1] / "results" / "events.csv")
    return parser


class EventLogger:
    """Append only final-state or connection changes, not every frame."""
    def __init__(self, path):
        self.path = Path(path)
        self.previous = None
        self._lock = threading.Lock()

    def record(self, posture, sensor_status, final_status, reason="", alert_kind=""):
        with self._lock:
            return self._record(posture, sensor_status, final_status, reason, alert_kind)

    def _record(self, posture, sensor_status, final_status, reason, alert_kind):
        key = (final_status, sensor_status == "SENSOR_DISCONNECTED")
        if key == self.previous and not alert_kind:
            return False
        self.path.parent.mkdir(parents=True, exist_ok=True)
        header = not self.path.exists() or self.path.stat().st_size == 0
        fields = ["timestamp", "posture", "sensor_status", "final_status", "reason", "alert_kind"]
        if not header:
            with self.path.open(encoding="utf-8", newline="") as existing:
                fields = next(csv.reader(existing))
        with self.path.open("a", newline="", encoding="utf-8") as output:
            writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
            if header:
                writer.writeheader()
            writer.writerow(dict(timestamp=datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
                                 posture=posture, sensor_status=sensor_status, final_status=final_status,
                                 reason=reason, alert_kind=alert_kind))
        if alert_kind != "EARLY_WARNING":
            self.previous = key
        return True


def draw_overlay(frame, posture, sensor, final_status, video_seconds=None):
    import cv2
    colors = {"NORMAL": (70, 210, 70), "SUSPICIOUS": (0, 200, 255),
              "FALL_DETECTED": (20, 20, 255)}
    color = colors[final_status]
    if sensor.risk_active and final_status != "FALL_DETECTED":
        color = (0, 100, 255) if int(time.monotonic()*2.5) % 2 else (0, 230, 255)
        cv2.rectangle(frame, (2, 2), (frame.shape[1]-3, frame.shape[0]-3), color, 8)
    values = ("--" if sensor.accel_total is None else f"{sensor.accel_total:.2f}",
              "--" if sensor.gyro_total is None else f"{sensor.gyro_total:.1f}")
    lines = [f"FINAL: {'EARLY WARNING' if sensor.risk_active and final_status != 'FALL_DETECTED' else final_status}", f"Posture: {posture.status}",
             f"Sensor: {sensor.status}", f"Accel: {values[0]} g | Gyro: {values[1]} deg/s",
             f"Pose: {posture.reason}", "Per-person vision | single-person IMU | q: quit"]
    if video_seconds is not None:
        lines.append(f"Video: {video_seconds:.1f} s | {'video only' if sensor.status == 'VIDEO_ONLY' else 'live Wokwi'}")
    cv2.rectangle(frame, (0, 0), (min(frame.shape[1], 600), len(lines)*27+12), (25, 25, 25), -1)
    for index, line in enumerate(lines):
        cv2.putText(frame, line, (12, 27 + index * 27), cv2.FONT_HERSHEY_SIMPLEX,
                    .6, color if index == 0 else (240, 240, 240), 2, cv2.LINE_AA)
    if final_status == "FALL_DETECTED":
        cv2.rectangle(frame, (2, 2), (frame.shape[1]-3, frame.shape[0]-3), color, 8)
        cv2.putText(frame, "FALL ALERT", (15, frame.shape[0]-22),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, color, 3, cv2.LINE_AA)
    return frame


def show_image(args):
    """Static images never enter sensor/fusion/event logging."""
    import cv2
    if not args.path or not Path(args.path).is_file():
        raise ValueError("Anh khong ton tai. Dung --path duong_dan_anh")
    frame = cv2.imread(str(args.path))
    if frame is None:
        raise ValueError("Khong doc duoc anh.")
    result = PoseDetector().detect(frame)
    posture = posture_from_result(result)
    frame = result.plot(conf=True, kpt_line=True)
    # Fit high-resolution images into a normal desktop window.
    scale = min(1, 960 / frame.shape[1], 720 / frame.shape[0])
    if scale < 1:
        frame = cv2.resize(frame, None, fx=scale, fy=scale)
    frame = cv2.copyMakeBorder(frame, 100, 0, 0, max(0, 640-frame.shape[1]),
                               cv2.BORDER_CONSTANT, value=(25, 25, 25))
    for index, text in enumerate((f"Posture: {posture.status}",
                                 "Still image: posture only; cannot confirm a fall.",
                                 "q: quit")):
        cv2.putText(frame, text, (12, 28 + index*28), cv2.FONT_HERSHEY_SIMPLEX,
                    .55, (240, 240, 240), 1, cv2.LINE_AA)
    print("Ảnh tĩnh chỉ đánh giá tư thế, không đủ dữ liệu để kết luận té ngã", flush=True)
    print(f"Posture: {posture.status}", flush=True)
    window = "Image posture only - q to quit"
    cv2.imshow(window, frame)
    started = time.monotonic()
    while not args.duration or time.monotonic() - started < args.duration:
        if cv2.waitKey(50) & 0xFF == ord("q"):
            break
        if cv2.getWindowProperty(window, cv2.WND_PROP_VISIBLE) < 1:
            break
    return 0


@dataclass(frozen=True)
class FrameUpdate:
    frame: object
    posture: object
    sensor: object
    final: object
    video_seconds: float | None
    inference_ms: float = 0.0
    produced_at: float = 0.0
    motion_active: bool = False
    motion_event: bool = False
    motion_reason: str = "Camera: thân nghiêng nhanh; cần kiểm tra, chưa xác nhận té."


def validate_args(args):
    for name in ("accel_threshold", "gyro_threshold", "impact_window", "lying_hold",
                 "recovery_hold", "duration", "occlusion_grace", "lying_warning"):
        value = getattr(args, name)
        if not math.isfinite(value) or value < 0 or (name != "duration" and value == 0):
            raise ValueError(f"Invalid --{name.replace('_', '-')}")


def monitor_frames(args, stop=None, on_sensor=None):
    """Shared camera/sensor engine for Tkinter and console; no GUI calls here."""
    import cv2
    validate_args(args)
    stop = stop if stop is not None else threading.Event()
    capture = stream = None
    frames = 0
    video_only = args.source == "video" and not args.video_live_sensor
    try:
        logger = EventLogger(args.log)
        def sensor_update(sample):
            if on_sensor is not None:
                on_sensor(sample)
            if sample.risk_event:
                logger.record("UNKNOWN", sample.status, "SUSPICIOUS",
                              sample.risk_reason, "EARLY_WARNING")
        if not video_only:
            stream = SensorStream(args.port, args.accel_threshold, args.gyro_threshold,
                                  on_sample=sensor_update).start()
        capture = open_capture(args.source, args.path, args.camera)
        detector = PoseDetector()
        if stop.is_set():
            return
        scene = SceneAnalyzer(args)
        started = time.monotonic()
        fps = capture.get(cv2.CAP_PROP_FPS)
        fps = fps if math.isfinite(fps) and 0 < fps <= 240 else 25
        video_frame = 0
        while not stop.is_set() and (not args.duration or time.monotonic()-started < args.duration):
            if args.source == "video" and not video_only:
                target = int((time.monotonic()-started)*fps)
                while video_frame < target and not stop.is_set():
                    if not capture.grab():
                        break
                    video_frame += 1
            ok, frame = capture.read()
            video_frame += 1
            if not ok:
                if args.source == "webcam" or frames == 0:
                    raise RuntimeError("Khong doc duoc frame tu camera/video.")
                break
            inference_started = time.monotonic()
            result = detector.detect(frame)
            inference_ms = (time.monotonic()-inference_started)*1000
            now = started+(video_frame-1)/fps if video_only else time.monotonic()
            boxes = result.boxes.data.cpu().tolist() if len(result.boxes) else []
            sensor = SensorSnapshot("VIDEO_ONLY") if video_only else stream.snapshot(now)
            points = result.keypoints.data.cpu().tolist() if len(result.boxes) and result.keypoints is not None else []
            posture, final, motion_active, motion_event, motion_reason, labels = scene.update(
                frame, boxes, points, now, None if video_only else sensor)
            if motion_event:
                logger.record(posture.status, sensor.status, final.status,
                              motion_reason, "EARLY_WARNING")
            kind = "FALL" if final.alert else "LYING_CHECK" if final.warning else ""
            logger.record(posture.status, sensor.status, final.status, final.reason, kind)
            frames += 1
            annotated = result.plot(conf=True, kpt_line=True)
            for number, box, status in labels:
                cv2.putText(annotated, f"#{number} {status}", (int(box[0]), max(18, int(box[1])-8)),
                            cv2.FONT_HERSHEY_SIMPLEX, .5, (0, 255, 255), 1, cv2.LINE_AA)
            yield FrameUpdate(annotated, posture, sensor, final,
                              (video_frame-1)/fps if args.source == "video" else None,
                              inference_ms, time.monotonic(), motion_active, motion_event, motion_reason)
            if args.source == "video":
                stop.wait(max(0, min(.1, started+video_frame/fps-time.monotonic())))
    finally:
        if stream is not None:
            stream.close()
        if capture is not None:
            capture.release()


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = build_parser()
    args = parser.parse_args()
    try:
        validate_args(args)
    except ValueError as exc:
        parser.error(str(exc))
    import cv2
    updates = None
    notifier = AlertNotifier(sound=not args.no_alerts)
    frames = 0
    try:
        if args.source == "image":
            return show_image(args)
        risk_events = queue.SimpleQueue()
        def on_sensor(sample):
            if sample.risk_event:
                risk_events.put(sample.risk_reason)
        updates = monitor_frames(args, on_sensor=on_sensor)
        previous = None
        window = "FallDetection - q to quit"
        for update in updates:
            while not risk_events.empty():
                reason = risk_events.get()
                print(f"EARLY_WARNING: {reason}", flush=True)
                if not args.no_alerts:
                    notifier.show("EARLY_WARNING", reason)
            if update.motion_event:
                reason = update.motion_reason
                print(f"EARLY_WARNING: {reason}", flush=True)
                if not args.no_alerts:
                    notifier.show("EARLY_WARNING", reason)
            final = update.final
            state = (update.posture.status, update.sensor.status, final.status)
            if state != previous or final.alert or final.warning:
                print(f"Posture: {state[0]} | Sensor: {state[1]} | Final: {state[2]} | {final.reason}", flush=True)
                previous = state
            if final.alert or final.warning:
                kind = "FALL" if final.alert else "LYING_CHECK"
                print(f"{kind}: {final.reason}", flush=True)
                if not args.no_alerts:
                    notifier.show(kind, final.reason)
            frame = draw_overlay(update.frame, update.posture, update.sensor, final.status,
                                 update.video_seconds)
            cv2.imshow(window, frame)
            notifier.tick()
            frames += 1
            if cv2.waitKey(1) & 0xFF == ord("q"):
                notifier.acknowledge()
                break
            if cv2.getWindowProperty(window, cv2.WND_PROP_VISIBLE) < 1:
                notifier.acknowledge()
                break
        updates.close()
        print(f"Demo stopped cleanly; frames: {frames}")
        # Keep an unacknowledged alert visible even when a video reaches EOF.
        while notifier.window is not None:
            notifier.tick()
            time.sleep(.03)
    except KeyboardInterrupt:
        print("\nDung demo.")
    except (OSError, RuntimeError, ValueError, cv2.error) as exc:
        print(f"Loi demo: {exc}")
        return 1
    finally:
        if updates is not None:
            updates.close()
        notifier.close()
        cv2.destroyAllWindows()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
