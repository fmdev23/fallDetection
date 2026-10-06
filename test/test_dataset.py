from collections import Counter
import unittest
from tools.prepare_urfall import sequence_splits, LABELS
from tools.label_video import validate_interval


class DatasetTests(unittest.TestCase):
    def test_sequence_partition_is_reproducible_and_stratified(self):
        split = sequence_splits()
        self.assertEqual(split, sequence_splits())
        self.assertEqual(len(split), 70)
        self.assertEqual(Counter(split.values()), {'train': 42, 'validation': 14, 'test': 14})
        for name, expected in [('train', (18, 24)), ('validation', (6, 8)), ('test', (6, 8))]:
            counts = Counter(k.split('-')[0] for k, v in split.items() if v == name)
            self.assertEqual((counts['fall'], counts['adl']), expected)

    def test_source_labels_are_not_invented_activity_or_fall_confirmation(self):
        self.assertEqual(LABELS[-1], 'not_lying')
        self.assertEqual(LABELS[0], 'falling_transition')
        self.assertEqual(LABELS[1], 'lying_on_ground')

    def test_annotation_rejects_overlap_invalid_bounds_and_missing_reviewer(self):
        rows = [dict(sha256='same', start_frame=10, end_frame=20)]
        for start, end, label, reviewer in [(20, 25, 'lying', 'reviewer'),
                                           (-1, 5, 'lying', 'reviewer'),
                                           (21, 100, 'lying', 'reviewer'),
                                           (21, 25, 'predicted_fall', 'reviewer'),
                                           (21, 25, 'lying', '')]:
            with self.subTest(start=start, end=end, label=label, reviewer=reviewer):
                with self.assertRaises(ValueError):
                    validate_interval(rows, 'same', start, end, 100, label, reviewer)
        validate_interval(rows, 'same', 21, 25, 100, 'lying', 'reviewer')
        validate_interval(rows, 'another', 10, 20, 100, 'lying', 'reviewer')


if __name__ == '__main__':
    unittest.main()
