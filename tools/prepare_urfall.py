"""Download the small official URFD previews, preserve labels and audit provenance.

No depth features are used as RGB features. Frame labels remain depth annotations:
matching frame counts alone does NOT prove exact RGB/depth synchronization.
"""
import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
import csv
import hashlib
import json
from pathlib import Path
import random
import time
import urllib.request

BASE = 'https://fenix.ur.edu.pl/~mkepski/ds/data/'
ROOT = Path(__file__).resolve().parents[1] / 'data' / 'urfall'
LABELS = {-1: 'not_lying', 0: 'falling_transition', 1: 'lying_on_ground'}


def sequence_splits():
    """60/20/20 stratified by sequence, never random frames; no subject claims."""
    splits = {}
    rng = random.Random(20261005)
    for kind, count in [('fall', 30), ('adl', 40)]:
        names = [f'{kind}-{i:02d}' for i in range(1, count+1)]
        rng.shuffle(names)
        for i, name in enumerate(names):
            splits[name] = 'train' if i < count*.6 else 'validation' if i < count*.8 else 'test'
    return splits


def fetch(name, root):
    path = root / 'source' / name
    url = BASE + name
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, method='HEAD'), timeout=30) as r:
                expected = int(r.headers['Content-Length'])
            if expected > 8_000_000:
                raise ValueError(f'Unexpectedly large preview/CSV: {name}')
            if not path.exists() or path.stat().st_size != expected:
                part = path.with_suffix(path.suffix+'.part')
                with urllib.request.urlopen(url, timeout=60) as r, part.open('wb') as output:
                    total = 0
                    while chunk := r.read(65536):
                        total += len(chunk)
                        if total > expected:
                            raise ValueError(f'Content size changed: {name}')
                        output.write(chunk)
                if part.stat().st_size != expected:
                    raise ValueError(f'Incomplete download: {name}')
                part.replace(path)
            return {'file': name, 'url': url, 'bytes': expected,
                    'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
        except (OSError, ValueError):
            if attempt == 2:
                raise
            time.sleep(attempt+1)


def write_csv(path, fields, rows):
    with path.open('w', encoding='utf-8', newline='') as output:
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def build(root):
    import cv2
    splits = sequence_splits()
    labels = defaultdict(dict)
    for filename in ('urfall-cam0-falls.csv', 'urfall-cam0-adls.csv'):
        with (root/'source'/filename).open(newline='') as source:
            for row in csv.reader(source):
                sequence, frame, label = row[0], int(row[1]), int(row[2])
                if label not in LABELS or frame in labels[sequence]:
                    raise ValueError(f'Invalid/duplicate annotation: {row[:3]}')
                labels[sequence][frame] = label
    manifest, annotations, issues = [], [], []
    (root/'rgb').mkdir(exist_ok=True)
    hashes = set()
    for sequence in sorted(splits):
        path = root/'source'/f'{sequence}-cam0.mp4'
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest in hashes:
            raise ValueError(f'Duplicate video: {sequence}')
        hashes.add(digest)
        cap = cv2.VideoCapture(str(path))
        fps = cap.get(cv2.CAP_PROP_FPS)
        rgb_path = root/'rgb'/f'{sequence}.mp4'
        writer = cv2.VideoWriter(str(rgb_path), cv2.VideoWriter_fourcc(*'mp4v'), fps, (320, 240))
        if not writer.isOpened():
            cap.release()
            raise RuntimeError('Cannot create RGB crop')
        frames = 0
        shape = None
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            shape = frame.shape
            if shape[:2] != (240, 640):
                writer.release()
                cap.release()
                raise ValueError(f'Unexpected preview layout: {sequence}, {shape}')
            writer.write(frame[:, 320:640])
            frames += 1
        cap.release()
        writer.release()
        if not shape or shape[:2] != (240, 640) or fps <= 0:
            raise ValueError(f'Unexpected preview layout: {sequence}, {shape}, {fps}')
        with (root/'source'/f'{sequence}-data.csv').open(newline='') as source:
            sync = {int(r[0]): (float(r[1]), float(r[2]) if len(r) > 2 else '')
                    for r in csv.reader(source) if r}
        complete = set(labels[sequence]) == set(range(1, frames+1)) == set(sync)
        alignment = 'count_match_not_rgb_verified' if complete else 'frame_count_mismatch'
        if not complete:
            issues.append({'sequence': sequence, 'decoded_frames': frames,
                           'label_frames': len(labels[sequence]), 'sync_frames': len(sync)})
        manifest.append(dict(sequence=sequence, split=splits[sequence],
                             sequence_label='fall' if sequence.startswith('fall') else 'non_fall_adl',
                             video=f'rgb/{rgb_path.name}', source_video=f'source/{path.name}',
                             source_sha256=digest, rgb_sha256=hashlib.sha256(rgb_path.read_bytes()).hexdigest(), frames=frames, fps=fps,
                             rgb_crop='320,0,640,240', subject_id='unknown',
                             frame_alignment=alignment))
        for frame, label in sorted(labels[sequence].items()):
            timestamp, accel = sync.get(frame, ('', ''))
            annotations.append(dict(sequence=sequence, split=splits[sequence], frame_1based=frame,
                                    depth_label=label, label_name=LABELS[label],
                                    source_time_ms=timestamp, accel_total_g=accel,
                                    rgb_alignment=alignment, fine_activity='unlabeled'))
    write_csv(root/'manifest.csv', list(manifest[0]), manifest)
    write_csv(root/'depth_annotations.csv', list(annotations[0]), annotations)
    report = dict(sequences=len(manifest), decoded_frames=sum(m['frames'] for m in manifest),
                  sequence_classes=dict(Counter(m['sequence_label'] for m in manifest)),
                  split_counts=dict(Counter(m['split'] for m in manifest)),
                  depth_label_counts=dict(Counter(a['label_name'] for a in annotations)),
                  unique_video_hashes=len(hashes), alignment_issues=issues,
                  source_bytes=sum(p.stat().st_size for p in (root/'source').iterdir() if p.is_file()),
                  rgb_bytes=sum(p.stat().st_size for p in (root/'rgb').glob('*.mp4')),
                  ready_for='Sequence-level fall/non-fall experiments using RGB crop; NOT fine activity or pre-fall ground truth',
                  subject_independent=False, exact_rgb_frame_labels_verified=False)
    (root/'audit.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--offline', action='store_true', help='Re-audit already downloaded files')
    args = parser.parse_args()
    (args.root/'source').mkdir(parents=True, exist_ok=True)
    names = ['urfall-cam0-falls.csv', 'urfall-cam0-adls.csv']
    for sequence in sorted(sequence_splits()):
        names.extend([f'{sequence}-cam0.mp4', f'{sequence}-data.csv'])
    if not args.offline:
        with ThreadPoolExecutor(max_workers=4) as pool:
            provenance = []
            for i, item in enumerate(pool.map(lambda name: fetch(name, args.root), names), 1):
                provenance.append(item)
                if i % 20 == 0:
                    print(f'Download verified: {i}/{len(names)}', flush=True)
        (args.root/'provenance.json').write_text(json.dumps(provenance, indent=2), encoding='utf-8')
    build(args.root)


if __name__ == '__main__':
    main()
