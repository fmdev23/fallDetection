import csv
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from python_app.evaluation import evaluate


class EvaluationTests(unittest.TestCase):
    def test_known_confusion_matrix(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / 'labels.csv'
            with manifest.open('w', newline='') as output:
                writer = csv.writer(output)
                writer.writerow(['scenario_id', 'source', 'expected_fall', 'event_log'])
                for index, (expected, final) in enumerate(((1, 'FALL_DETECTED'),
                        (0, 'FALL_DETECTED'), (0, 'NORMAL'), (1, 'SUSPICIOUS'))):
                    log = root / f'{index}.csv'
                    log.write_text(f'final_status\n{final}\n')
                    writer.writerow([index, 'webcam', expected, log.name])
            result = evaluate(manifest)
            self.assertEqual([result[k] for k in ('TP', 'FP', 'TN', 'FN')], [1, 1, 1, 1])
            self.assertEqual([result[k] for k in ('Accuracy', 'Precision', 'Recall', 'F1')], [.5]*4)

    def test_no_ground_truth_is_not_a_score(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'empty.csv'
            path.write_text('scenario_id,source,expected_fall,event_log\n')
            with self.assertRaisesRegex(ValueError, 'No labelled trials'):
                evaluate(path)


if __name__ == '__main__':
    unittest.main()
