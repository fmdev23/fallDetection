"""Controlled pipeline tests, not measured camera/dataset accuracy."""

import csv
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch
import unittest
import itertools

from python_app.fall_fusion import FallFusion
from python_app.posture_analyzer import analyze_posture
from python_app.sensor_analyzer import analyze_sensor
from python_app.sensor_reader import SensorSnapshot, parse_sensor_line
from python_app import main


class PipelineTests(unittest.TestCase):
    def test_video_only_keeps_every_frame_and_uses_clip_clock_not_processing_time(self):
        import numpy as np
        frame = np.zeros((240, 320, 3), dtype=np.uint8)
        capture = MagicMock()
        capture.read.side_effect = [(True, frame)]*3 + [(False, None)]
        capture.get.return_value = 30
        result = MagicMock()
        result.boxes.__len__.return_value = 1
        result.boxes.data.cpu().tolist.return_value = [[100, 50, 310, 140, .9]]
        points = [[0, 0, 0] for _ in range(17)]
        for index, x in ((5, 100), (11, 200), (13, 300)):
            points[index] = [x, 100, .9]
        result.keypoints.data.cpu().tolist.return_value = [points]
        result.plot.return_value = frame
        with TemporaryDirectory() as folder:
            args = main.build_parser().parse_args(['--source', 'video', '--path', 'clip.mp4',
                                                  '--log', str(Path(folder)/'events.csv')])
            with (patch.object(main, 'open_capture', return_value=capture),
                  patch.object(main, 'PoseDetector') as detector,
                  patch.object(main, 'SensorStream') as reader,
                  patch.object(main.time, 'monotonic', side_effect=itertools.count(10, .8))):
                detector.return_value.detect.return_value = result
                frames = list(main.monitor_frames(args))
            self.assertEqual([u.video_seconds for u in frames], [0, 1/30, 2/30])
            self.assertAlmostEqual(frames[-1].final.lying_seconds, 2/30)
            self.assertFalse(any(u.final.warning or u.final.alert for u in frames))
            self.assertTrue(all(u.sensor.status == 'VIDEO_ONLY' for u in frames))
            reader.assert_not_called()
            capture.grab.assert_not_called()
            capture.release.assert_called_once()

    def test_sensor_packet_to_final_state_and_event_log(self):
        upright = [[0, 0, 0] for _ in range(17)]
        lying = [[0, 0, 0] for _ in range(17)]
        for i, y in ((5, 100), (11, 200), (13, 300)):
            upright[i] = [100, y, .9]
            lying[i] = [y, 100, .9]
        cases = [
            (upright, 'SENSOR,0,0,1,0,0,0', 'NORMAL'),
            (upright, 'SENSOR,0,0,1,200,0,0', 'SUSPICIOUS'),
            (lying, 'SENSOR,0,0,1,0,0,0', 'SUSPICIOUS'),
            (lying, 'SENSOR,0,0,1,200,0,0', 'FALL_DETECTED'),
        ]
        with TemporaryDirectory() as directory:
            for index, (points, packet, expected) in enumerate(cases):
                with self.subTest(expected=expected, packet=packet):
                    fusion = FallFusion()
                    path = Path(directory) / f'case{index}.csv'
                    logger = main.EventLogger(path)
                    alerts = 0
                    for step in range(10):
                        posture = analyze_posture(points).status
                        sensor = analyze_sensor(parse_sensor_line(packet)).status
                        final = fusion.update(posture, sensor, step * .5)
                        logger.record(posture, sensor, final.status)
                        alerts += final.alert
                    self.assertEqual(final.status, expected)
                    self.assertEqual(alerts, int(expected == 'FALL_DETECTED'))
                    with path.open() as source:
                        rows = list(csv.DictReader(source))
                    self.assertLessEqual(len(rows), 2)

    def test_q_closes_webcam_and_video_even_without_sensor_or_person(self):
        import numpy as np
        for source in ('webcam', 'video'):
            with self.subTest(source=source), TemporaryDirectory() as directory:
                frame = np.zeros((480, 640, 3), dtype=np.uint8)
                capture = MagicMock()
                capture.read.return_value = (True, frame)
                capture.get.return_value = 25
                result = MagicMock()
                result.keypoints = None
                result.boxes = []
                result.plot.return_value = frame
                stream = MagicMock()
                stream.snapshot.return_value = SensorSnapshot()
                with (patch('sys.argv', ['main', '--source', source, '--log',
                                        str(Path(directory) / 'events.csv')]),
                      patch.object(main, 'open_capture', return_value=capture),
                      patch.object(main, 'PoseDetector') as detector,
                      patch.object(main, 'SensorStream') as reader,
                      patch('cv2.imshow'), patch('cv2.waitKey', return_value=ord('q')),
                      patch('cv2.destroyAllWindows') as destroy):
                    detector.return_value.detect.return_value = result
                    reader.return_value.start.return_value = stream
                    self.assertEqual(main.main(), 0)
                    capture.release.assert_called_once()
                    if source == "webcam":
                        stream.close.assert_called_once()
                    else:
                        reader.assert_not_called()
                    destroy.assert_called_once()


if __name__ == '__main__':
    unittest.main()
