"""Replay cached detections to audit temporal/scale logic, NOT detector accuracy."""
import argparse
import copy
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from python_app.main import build_parser
from python_app.scene_analyzer import SceneAnalyzer


def main():
    import cv2
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('video')
    parser.add_argument('cache', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    cached = json.loads(args.cache.read_text(encoding='utf-8'))
    variants = [(1, 1, 1, False), (2, 1, 1, False), (3, 1, 1, False),
                (1, .5, 1, False), (1, 1, 1, True), (1, 1, .75, False), (1, 1, 1.25, False)]
    reports = []
    for stride, scale, speed, mirror in variants:
        capture = cv2.VideoCapture(args.video)
        engine = SceneAnalyzer(build_parser().parse_args([]))
        events = []
        for i, original in enumerate(cached):
            ok, frame = capture.read()
            if not ok:
                raise ValueError('Cache/video frame count mismatch')
            if i % stride:
                continue
            row = copy.deepcopy(original)
            if mirror:
                frame = cv2.flip(frame, 1)
                width = frame.shape[1]
                for box in row['boxes']:
                    box[0], box[2] = width-box[2], width-box[0]
                for points in row['keypoints']:
                    for point in points:
                        point[0] = width-point[0]
            if scale != 1:
                frame = cv2.resize(frame, None, fx=scale, fy=scale)
                for box in row['boxes']:
                    box[:4] = [v*scale for v in box[:4]]
                for points in row['keypoints']:
                    for point in points:
                        point[:2] = [v*scale for v in point[:2]]
            _, final, _, event, reason, _ = engine.update(frame, row['boxes'], row['keypoints'], row['t']/speed)
            if event or final.warning or final.alert:
                events.append({'source_seconds': round(row['t'], 3), 'early': event,
                               'lying': final.warning, 'fall': final.alert})
        capture.release()
        reports.append(dict(stride=stride, scale=scale, speed=speed, mirror=mirror, events=events))
        print(json.dumps(reports[-1]), flush=True)
    args.output.write_text(json.dumps({'scope': 'cached detector outputs; logic and optical flow only',
                                      'variants': reports}, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
