"""Standalone YOLO11n Pose webcam/video demo (no sensor needed)."""

import argparse
import math
from pathlib import Path
import sys
import time

MODEL_PATH = Path(__file__).resolve().parents[1] / "yolo11n-pose.pt"


class PoseDetector:
    def __init__(self, confidence=0.5, image_size=480):
        from ultralytics import YOLO
        self.model = YOLO(str(MODEL_PATH))
        self.confidence = confidence
        self.image_size = image_size

    def detect(self, frame):
        return self.model.predict(frame, conf=self.confidence,
                                  imgsz=self.image_size, device="cpu",
                                  verbose=False)[0]


def open_capture(source, path=None, camera=0):
    import cv2
    if source == "video":
        if not path or not Path(path).is_file():
            raise ValueError("Video khong ton tai. Dung --path duong_dan_video")
        capture = cv2.VideoCapture(str(path))
    else:
        # DirectShow avoids long Media Foundation startup on some Windows PCs.
        capture = cv2.VideoCapture(camera, cv2.CAP_DSHOW) if sys.platform == "win32" else cv2.VideoCapture(camera)
        if not capture.isOpened() and sys.platform == "win32":
            capture.release()
            capture = cv2.VideoCapture(camera)
        capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Backend may ignore this hint.
    if not capture.isOpened():
        capture.release()
        raise RuntimeError("Khong mo duoc camera/video. Kiem tra quyen camera va --camera.")
    return capture


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=("webcam", "video"), default="webcam")
    parser.add_argument("--path")
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--duration", type=float, default=0,
                        help="Optional finite demo duration in seconds")
    args = parser.parse_args()
    if not math.isfinite(args.duration) or args.duration < 0:
        parser.error("--duration must be finite and nonnegative")
    import cv2
    capture = None
    frames = people_frames = 0
    try:
        capture = open_capture(args.source, args.path, args.camera)
        detector = PoseDetector()
        start = time.monotonic()
        window = "YOLO11n Pose - q to quit"
        while not args.duration or time.monotonic() - start < args.duration:
            ok, frame = capture.read()
            if not ok:
                if args.source == "webcam" or frames == 0:
                    raise RuntimeError("Khong doc duoc frame tu camera/video.")
                break
            result = detector.detect(frame)
            frames += 1
            people_frames += int(len(result.boxes) > 0)
            cv2.imshow(window, result.plot(conf=True, kpt_line=True))
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
            if cv2.getWindowProperty(window, cv2.WND_PROP_VISIBLE) < 1:
                break
        print(f"Frames: {frames}; frames with person: {people_frames}")
    except KeyboardInterrupt:
        pass
    except (OSError, RuntimeError, ValueError, cv2.error) as exc:
        print(f"Loi vision: {exc}")
        return 1
    finally:
        if capture is not None:
            capture.release()
        cv2.destroyAllWindows()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
