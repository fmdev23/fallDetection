"""Summarize manually labelled trials; never invent ground truth from poses."""

import argparse
import csv
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]


def evaluate(manifest):
    manifest = Path(manifest)
    counts = dict(TP=0, FP=0, TN=0, FN=0)
    ids = set()
    used_logs = set()
    with manifest.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        required = {"scenario_id", "source", "expected_fall", "event_log"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("Manifest needs scenario_id,source,expected_fall,event_log")
        for row in reader:
            name = (row.get("scenario_id") or "").strip()
            if not name or name in ids:
                raise ValueError("Each trial needs a unique nonempty scenario_id")
            expected = (row.get("expected_fall") or "").strip()
            if expected not in ("0", "1"):
                raise ValueError(f"{name}: assign expected_fall=0 or 1 manually first")
            video = (row.get("source") or "").strip()
            if not video or (video != "webcam" and not (manifest.parent / video).is_file()):
                raise ValueError(f"{name}: source must be webcam or an existing video")
            event_file = (row.get("event_log") or "").strip()
            if not event_file:
                raise ValueError(f"{name}: event_log is required")
            event_path = (manifest.parent / event_file).resolve()
            if event_path in used_logs:
                raise ValueError(f"{name}: use a separate event log for every trial")
            with event_path.open(encoding="utf-8-sig", newline="") as events:
                records = list(csv.DictReader(events))
            if not records or any(r.get("final_status") not in
                                  ("NORMAL", "SUSPICIOUS", "FALL_DETECTED") for r in records):
                raise ValueError(f"{name}: empty or invalid event log")
            predicted = any(r["final_status"] == "FALL_DETECTED" for r in records)
            label = ("TP" if predicted else "FN") if expected == "1" else ("FP" if predicted else "TN")
            counts[label] += 1
            ids.add(name)
            used_logs.add(event_path)
    if not ids:
        raise ValueError("No labelled trials. Fill the manifest after running and labelling real trials.")
    tp, fp, tn, fn = (counts[key] for key in ("TP", "FP", "TN", "FN"))

    def ratio(numerator, denominator):
        return numerator / denominator if denominator else None

    return {"trials": len(ids), **counts, "Accuracy": ratio(tp+tn, len(ids)),
            "Precision": ratio(tp, tp+fp), "Recall": ratio(tp, tp+fn),
            "F1": ratio(2*tp, 2*tp+fp+fn)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=PROJECT / "test_videos" / "evaluation.csv")
    parser.add_argument("--output", type=Path, help="Optional summary CSV")
    args = parser.parse_args()
    try:
        result = evaluate(args.manifest)
        for key, value in result.items():
            print(f"{key}: {'N/A' if value is None else value}")
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open("w", newline="", encoding="utf-8") as output:
                writer = csv.DictWriter(output, fieldnames=list(result))
                writer.writeheader()
                writer.writerow({k: "N/A" if v is None else v for k, v in result.items()})
    except (OSError, ValueError) as exc:
        print(f"Evaluation unavailable: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
