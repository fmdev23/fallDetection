from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch
import unittest
from python_app import main


class ImageTests(unittest.TestCase):
    def test_image_never_enters_fusion_or_sensor(self):
        import cv2
        import numpy as np
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'input.png'
            frame = np.zeros((200, 640, 3), dtype=np.uint8)
            self.assertTrue(cv2.imwrite(str(path), frame))
            result = MagicMock()
            result.boxes = []
            result.keypoints = None
            result.plot.return_value = frame
            with (patch('sys.argv', ['main', '--source', 'image', '--path', str(path)]),
                  patch.object(main, 'PoseDetector') as detector,
                  patch.object(main, 'SensorStream') as stream,
                  patch.object(main, 'SceneAnalyzer') as scene,
                  patch.object(main, 'EventLogger') as logger,
                  patch('cv2.imshow'), patch('cv2.waitKey', return_value=ord('q')),
                  patch('cv2.destroyAllWindows')):
                detector.return_value.detect.return_value = result
                self.assertEqual(main.main(), 0)
                stream.assert_not_called()
                scene.assert_not_called()
                logger.assert_not_called()


if __name__ == '__main__':
    unittest.main()
