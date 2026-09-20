"""
S.P.O.T. reproducible held-out model benchmark (old 4-class vs Arena binary).

Scores BOTH committed onoin classifiers on the SAME held-out image set:

  * Arena binary model (current /inspect path):
      artifacts/ml/experiments/yolo26n_cls_pilot_v1/weights/best.pt
      classes {0: defective, 1: healthy}
  * Legacy 4-class model (/analyze-onion path):
      backend/models/onion_classifier.pt
      classes {0: disease, 1: healthy, 2: rotten, 3: sprouted}
      mapped to binary for comparison: {disease, rotten, sprouted} -> defective

For each model it reports (computed at runtime, nothing hard-coded):
  accuracy, per-class precision/recall/F1, confusion matrix, healthy recall,
  defective recall, false positives, false negatives, CPU inference latency
  (mean, p95), and on-disk model size.

The held-out images must be supplied by the caller (they are intentionally NOT
committed). A ground-truth manifest guarantees the labels are explicit and
checksum-verified so images cannot be silently swapped or relabelled.

Usage:
  .venv/bin/python scripts/evaluate_models.py \
      --images artifacts/ml/v1_eval/images \
      --manifest artifacts/ml/v1_eval/manifest.csv \
      --out artifacts/ml/v1_eval/results.json

Manifest CSV columns (header required):
  filename,class,source_note,checksum_sha256
    filename         : basename of the image inside --images (e.g. eval_001.jpg)
    class            : exactly "healthy" or "defective" (ground truth)
    source_note      : free-text provenance (dataset/source URL); recorded, never used for scoring
    checksum_sha256  : hex SHA-256 of the image file (verified before scoring)

Leakage prevention (runs before scoring, aborts on violation):
  * every eval filename/basename is checked against the committed legacy
    split manifest (artifacts/ml/split_manifest.json) train/val/test filenames;
  * every eval `filename` (sans extension) is checked against committed pilot
    annotation records + the pilot annotation manifest IDs;
  * unknown/blank ground-truth labels are an error, never a prediction.
"""

import argparse
import csv
import hashlib
import json
import os
import sys
import time
from typing import Dict, List, Optional

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# (repo-relative path, role) for the two models under comparison.
MODELS = [
    {
        "key": "arena_binary_best.pt",
        "role": "Arena binary classifier (serves /api/v1/inspect)",
        "rel_path": os.path.join(
            "artifacts", "ml", "experiments", "yolo26n_cls_pilot_v1", "weights", "best.pt"
        ),
        "binary": True,
    },
    {
        "key": "legacy_4class_onion_classifier.pt",
        "role": "Legacy 4-class classifier (serves /api/v1/analyze-onion)",
        "rel_path": os.path.join("backend", "models", "onion_classifier.pt"),
        "binary": False,
    },
]

# Labels every model must be reduced to for the comparison.
TRUE_LABELS = ("healthy", "defective")

# 4-class classes that map to the binary "defective" side.
LEGACY_DEFECTIVE_NAMES = {"disease", "rotten", "sprouted", "damage", "defective"}


def percentile(sorted_values: List[float], p: float) -> float:
    """Linear-interpolation percentile (numpy `linear` method) on a sorted list."""
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return sorted_values[0]
    rank = (p / 100.0) * (len(sorted_values) - 1)
    lo = int(rank)
    hi = min(lo + 1, len(sorted_values) - 1)
    frac = rank - lo
    return sorted_values[lo] + frac * (sorted_values[hi] - sorted_values[lo])


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_manifest(path: str) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    if not os.path.exists(path):
        sys.exit(f"FATAL: manifest not found: {path}")
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"filename", "class", "source_note", "checksum_sha256"}
        missing = required - set(reader.fieldnames or ())
        if missing:
            sys.exit(f"FATAL: manifest missing columns: {sorted(missing)}")
        for row in reader:
            row = {k: (v or "").strip() for k, v in row.items()}
            if not row["filename"]:
                continue  # blank line
            rows.append(row)
    if not rows:
        sys.exit("FATAL: manifest contains no image rows")
    return rows


def build_known_indices() -> Dict[str, set]:
    """Collect committed identifiers that held-out images must NOT match.

    Returns {'path_tokens': set, 'basenames': set, 'pilot_ids': set}.
    """
    known_path_tokens: set = set()
    known_basenames: set = set()
    pilot_ids: set = set()

    split_manifest = os.path.join(PROJECT_ROOT, "artifacts", "ml", "split_manifest.json")
    if os.path.exists(split_manifest):
        with open(split_manifest, encoding="utf-8") as f:
            sm = json.load(f)
        for key in ("train_filenames", "val_filenames", "test_filenames", "leaf_filenames"):
            for p in sm.get(key, []):
                tok = str(p).strip().lower()
                known_path_tokens.add(tok)
                known_basenames.add(os.path.basename(tok))
    else:
        print("WARN: split_manifest.json absent; skipping legacy filename check")

    ann_dir = os.path.join(PROJECT_ROOT, "artifacts", "ml", "defect_annotations")
    ann_manifest = os.path.join(ann_dir, "annotation_manifest.json")
    if os.path.exists(ann_manifest):
        with open(ann_manifest, encoding="utf-8") as f:
            am = json.load(f)
        for img in am.get("stratified_images", []):
            iid = str(img.get("image_id", "")).strip()
            if iid:
                pilot_ids.add(iid.lower())

    records_dir = os.path.join(ann_dir, "records")
    if os.path.exists(records_dir):
        for fname in os.listdir(records_dir):
            if not fname.endswith(".json"):
                continue
            try:
                with open(os.path.join(records_dir, fname), encoding="utf-8") as f:
                    rec = json.load(f)
                for field in ("image_id", "pilot_id"):
                    v = str(rec.get(field, "")).strip()
                    if v:
                        pilot_ids.add(v.lower())
            except Exception:
                continue

    return {
        "path_tokens": known_path_tokens,
        "basenames": known_basenames,
        "pilot_ids": pilot_ids,
    }


def leakage_check(rows: List[Dict[str, str]], indices: Dict[str, set]) -> None:
    token_hits: List[str] = []
    pilot_hits: List[str] = []
    for row in rows:
        stem = os.path.splitext(row["filename"])[0].strip().lower()
        base = os.path.basename(row["filename"]).strip().lower()

        if base in indices["basenames"]:
            token_hits.append(f"{row['filename']} (basename matches a legacy split file)")
        if stem in indices["pilot_ids"] or base in indices["pilot_ids"]:
            pilot_hits.append(f"{row['filename']} (matches a pilot annotation id)")

    if token_hits or pilot_hits:
        msg = "FATAL: LEAKAGE DETECTED — held-out set overlaps committed training/split identifiers:\n"
        for h in token_hits + pilot_hits:
            msg += f"  - {h}\n"
        sys.exit(msg)
    print("[leakage-check] PASS: no eval image matches committed split/pilot identifiers")


def label_to_binary(name: Optional[str]) -> Optional[str]:
    """Normalize an arbitrary model class name to healthy/defective or None."""
    if name is None:
        return None
    n = str(name).strip().lower()
    if n == "healthy":
        return "healthy"
    if n in LEGACY_DEFECTIVE_NAMES:
        return "defective"
    return None


def score_model(model_key: str, role: str, ckpt: str, is_binary: bool,
                images: List[str], truths: List[str]) -> Dict:
    if not os.path.exists(ckpt):
        return {"key": model_key, "role": role, "checkpoint": ckpt, "status": "ABSENT"}

    from ultralytics import YOLO

    try:
        yolo = YOLO(ckpt)
        names = {int(k): str(v) for k, v in yolo.names.items()}
    except Exception as exc:  # noqa: BLE001
        return {"key": model_key, "role": role, "checkpoint": ckpt,
                "status": "LOAD_ERROR", "error": str(exc)}

    # Reject a checkpoint whose classes cannot map to healthy/defective.
    mapped = [label_to_binary(v) for v in names.values()]
    if any(m is None for m in mapped):
        return {"key": model_key, "role": role, "checkpoint": ckpt, "status": "UNSUPPORTED_CLASSES",
                "classes": names}

    size_bytes = os.path.getsize(ckpt)
    latencies: List[float] = []
    preds: List[str] = []
    confs: List[float] = []

    for img in images:
        t0 = time.perf_counter()
        r = yolo.predict(source=img, imgsz=224, device="cpu", verbose=False)[0]
        latencies.append((time.perf_counter() - t0) * 1000.0)
        probs = r.probs
        top = int(probs.top1)
        raw = names.get(top)
        preds.append(label_to_binary(raw) or "unknown")
        try:
            confs.append(float(probs.top1conf))
        except Exception:
            confs.append(float(max(probs.data.tolist())))

    # --- metrics ---
    n = len(truths)
    cm = {"healthy": {"healthy": 0, "defective": 0}, "defective": {"healthy": 0, "defective": 0}}
    for t, p in zip(truths, preds):
        if t in cm and p in cm[t]:
            cm[t][p] += 1

    def _per_class(cls: str) -> Dict:
        tp = cm[cls][cls]
        fp = cm["healthy"][cls] if cls == "defective" else cm["defective"][cls]
        fn = cm[cls]["defective"] if cls == "healthy" else cm[cls]["healthy"]
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        return {"precision": round(precision, 4), "recall": round(recall, 4),
                "f1": round(f1, 4), "tp": tp, "fp": fp, "fn": fn, "samples": tp + fn}

    correct = sum(1 for t, p in zip(truths, preds) if t == p)
    healthy = _per_class("healthy")
    defective = _per_class("defective")

    mean_lat = sum(latencies) / len(latencies) if latencies else 0.0
    p95_lat = percentile(sorted(latencies), 95.0) if latencies else 0.0

    return {
        "key": model_key,
        "role": role,
        "checkpoint": ckpt,
        "status": "OK",
        "classes": names,
        "size_bytes": size_bytes,
        "size_mb": round(size_bytes / (1024 * 1024), 3),
        "n_images": n,
        "accuracy": round(correct / n, 4) if n else None,
        "per_class": {"healthy": healthy, "defective": defective},
        "confusion_matrix_rows_truth": {
            "healthy": cm["healthy"],
            "defective": cm["defective"],
        },
        "false_positives_defective_class": defective["fp"],
        "false_negatives_defective_class": defective["fn"],
        "healthy_recall": healthy["recall"],
        "defective_recall": defective["recall"],
        "latency_ms_mean": round(mean_lat, 2),
        "latency_ms_p95": round(p95_lat, 2),
        "per_image": [
            {"file": os.path.basename(img), "truth": t, "pred": p,
             "conf": round(c, 4)}
            for img, t, p, c in zip(images, truths, preds, confs)
        ],
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--images", required=True, help="Directory of held-out images")
    ap.add_argument("--manifest", required=True, help="Ground-truth CSV manifest")
    ap.add_argument("--out", required=True, help="Output JSON path")
    ap.add_argument("--imgsz", type=int, default=224, help="Classifier input size (default 224)")
    args = ap.parse_args()

    if not os.path.isdir(args.images):
        sys.exit(f"FATAL: images directory not found: {args.images}")

    rows = load_manifest(args.manifest)

    images: List[str] = []
    truths: List[str] = []
    provenance: List[str] = []
    for row in rows:
        fname = row["filename"]
        cls = row["class"].strip().lower()
        if cls not in TRUE_LABELS:
            sys.exit(f"FATAL: manifest row {fname!r} has invalid class {row['class']!r} "
                     f"(must be healthy or defective)")
        path = os.path.join(args.images, fname)
        if not os.path.isfile(path):
            sys.exit(f"FATAL: manifest image missing on disk: {path}")
        actual = sha256_file(path)
        if row["checksum_sha256"].lower() != actual.lower():
            sys.exit(
                f"FATAL: checksum mismatch for {fname}\n"
                f"  manifest: {row['checksum_sha256']}\n"
                f"  actual:   {actual}\n"
                f"  label provenance ({row['source_note']}) may not match these bytes."
            )
        images.append(path)
        truths.append(cls)
        provenance.append(row["source_note"])

    print(f"[benchmark] held-out images: {len(images)} "
          f"(healthy={truths.count('healthy')}, defective={truths.count('defective')})")

    leakage_check(rows, build_known_indices())

    results = {
        "generated_by": "scripts/evaluate_models.py",
        "images_dir": os.path.abspath(args.images),
        "manifest": os.path.abspath(args.manifest),
        "imgsz": args.imgsz,
        "models": [
            score_model(
                m["key"], m["role"],
                os.path.join(PROJECT_ROOT, m["rel_path"]),
                m["binary"], images, truths,
            )
            for m in MODELS
        ],
    }

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"[benchmark] wrote {args.out}")

    # Human-readable summary
    print("\n" + "=" * 78)
    for m in results["models"]:
        print(f"MODEL: {m['key']}  [{m['status']}]")
        if m.get("status") != "OK":
            print(f"  {m.get('error', '') or m.get('classes', '')}")
            continue
        print(f"  role      : {m['role']}")
        print(f"  classes   : {m['classes']}   size={m['size_mb']} MB")
        print(f"  acc       : {m['accuracy']} (n={m['n_images']})")
        print(f"  healthy   : P={m['per_class']['healthy']['precision']} "
              f"R={m['per_class']['healthy']['recall']} "
              f"F1={m['per_class']['healthy']['f1']}")
        print(f"  defective : P={m['per_class']['defective']['precision']} "
              f"R={m['per_class']['defective']['recall']} "
              f"F1={m['per_class']['defective']['f1']}")
        print(f"  FP (defective class)={m['false_positives_defective_class']} "
              f"FN={m['false_negatives_defective_class']}")
        print(f"  latency   : mean={m['latency_ms_mean']} ms  p95={m['latency_ms_p95']} ms")
        print(f"  confusion (rows=truth): {m['confusion_matrix_rows_truth']}")
    print("=" * 78)


if __name__ == "__main__":
    main()
