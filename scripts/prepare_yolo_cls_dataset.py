"""
S.P.O.T. Phase 2 — Prepare YOLO-cls Dataset
=============================================
Reads the frozen pilot annotations and creates a binary classification
dataset (healthy vs defective) in YOLO-cls directory format.

Output: artifacts/ml/yolo_cls_dataset_v1/
"""

import datetime
import json
import os
import random
import shutil
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RECORDS_DIR = os.path.join(PROJECT_ROOT, "artifacts", "ml", "defect_annotations", "records")
PILOT_IMAGES_DIR = os.path.join(PROJECT_ROOT, "artifacts", "ml", "defect_annotations", "pilot_100", "images")
PILOT_MANIFEST = os.path.join(PROJECT_ROOT, "artifacts", "ml", "defect_annotations", "pilot_100", "manifest.csv")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "artifacts", "ml", "yolo_cls_dataset_v1")

ANNOTATOR_ID = "HUMAN_ANNOTATOR_A"
RANDOM_SEED = 42
VAL_RATIO = 0.20


def find_pilot_image(image_id: str) -> str | None:
    """Find the image file for a given pilot ID (e.g., pilot_001)."""
    for fname in os.listdir(PILOT_IMAGES_DIR):
        if fname.startswith(image_id + "_"):
            return os.path.join(PILOT_IMAGES_DIR, fname)
    return None


def main():
    print("=" * 70)
    print("S.P.O.T. Phase 2 — Prepare YOLO-cls Dataset")
    print("=" * 70)

    # ---- Step 1: Load HUMAN_ANNOTATOR_A records ----
    records = []
    for fname in sorted(os.listdir(RECORDS_DIR)):
        if not fname.endswith(".json"):
            continue
        with open(os.path.join(RECORDS_DIR, fname), "r", encoding="utf-8") as f:
            rec = json.load(f)
        if rec.get("annotator_id") == ANNOTATOR_ID:
            records.append(rec)

    print(f"\n[1/5] Loaded {len(records)} {ANNOTATOR_ID} records")

    # ---- Step 2: Classify into healthy / defective / excluded ----
    healthy_samples = []
    defective_samples = []
    excluded_samples = []

    for rec in records:
        image_id = rec["image_id"]
        defects = rec.get("multi_label_defects", {})

        is_healthy = defects.get("healthy", False)
        has_damage = defects.get("damage", False)
        has_rot = defects.get("rot", False)
        has_sprout = defects.get("sprout", False)
        has_any_defect = has_damage or has_rot or has_sprout

        # Find corresponding image
        img_path = find_pilot_image(image_id)
        if img_path is None:
            print(f"  ⚠️  No image found for {image_id} — excluding")
            excluded_samples.append({"image_id": image_id, "reason": "NO_IMAGE_FILE"})
            continue

        if has_any_defect:
            defective_samples.append({
                "image_id": image_id,
                "image_path": img_path,
                "class": "defective",
                "defects": {
                    "damage": has_damage,
                    "rot": has_rot,
                    "sprout": has_sprout,
                },
                "confidence": rec.get("annotation_confidence", ""),
            })
        elif is_healthy:
            healthy_samples.append({
                "image_id": image_id,
                "image_path": img_path,
                "class": "healthy",
                "confidence": rec.get("annotation_confidence", ""),
            })
        else:
            # No healthy flag AND no defect flags — uncertain-only
            excluded_samples.append({
                "image_id": image_id,
                "reason": "UNCERTAIN_ONLY_NO_LABEL",
            })

    total_usable = len(healthy_samples) + len(defective_samples)
    print(f"[2/5] Classification complete:")
    print(f"  Healthy:    {len(healthy_samples)}")
    print(f"  Defective:  {len(defective_samples)}")
    print(f"  Excluded:   {len(excluded_samples)} ({[e['image_id'] for e in excluded_samples]})")
    print(f"  Total usable: {total_usable}")

    # ---- Step 3: Stratified train/val split ----
    random.seed(RANDOM_SEED)

    def split_list(items, val_ratio):
        shuffled = list(items)
        random.shuffle(shuffled)
        n_val = max(1, int(len(shuffled) * val_ratio))
        return shuffled[n_val:], shuffled[:n_val]

    train_healthy, val_healthy = split_list(healthy_samples, VAL_RATIO)
    train_defective, val_defective = split_list(defective_samples, VAL_RATIO)

    print(f"[3/5] Stratified split (seed={RANDOM_SEED}, val_ratio={VAL_RATIO}):")
    print(f"  Train: {len(train_healthy)} healthy + {len(train_defective)} defective = {len(train_healthy) + len(train_defective)}")
    print(f"  Val:   {len(val_healthy)} healthy + {len(val_defective)} defective = {len(val_healthy) + len(val_defective)}")

    # ---- Step 4: Create YOLO-cls directory structure ----
    # Clean output directory if it exists
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)

    for split in ["train", "val"]:
        for cls in ["healthy", "defective"]:
            os.makedirs(os.path.join(OUTPUT_DIR, split, cls), exist_ok=True)

    def copy_samples(samples, split_name):
        for s in samples:
            src = s["image_path"]
            cls = s["class"]
            fname = os.path.basename(src)
            dst = os.path.join(OUTPUT_DIR, split_name, cls, fname)
            shutil.copy2(src, dst)

    copy_samples(train_healthy, "train")
    copy_samples(train_defective, "train")
    copy_samples(val_healthy, "val")
    copy_samples(val_defective, "val")

    # Count copied files
    train_count = sum(len(os.listdir(os.path.join(OUTPUT_DIR, "train", c))) for c in ["healthy", "defective"])
    val_count = sum(len(os.listdir(os.path.join(OUTPUT_DIR, "val", c))) for c in ["healthy", "defective"])

    print(f"[4/5] ✅ Created YOLO-cls directory structure:")
    print(f"  {OUTPUT_DIR}/")
    print(f"    train/ ({train_count} images)")
    print(f"      healthy/    ({len(train_healthy)})")
    print(f"      defective/  ({len(train_defective)})")
    print(f"    val/ ({val_count} images)")
    print(f"      healthy/    ({len(val_healthy)})")
    print(f"      defective/  ({len(val_defective)})")

    # ---- Step 5: Generate dataset metadata ----
    meta = {
        "dataset_name": "SPOT-PILOT-YOLO-CLS-V1",
        "dataset_version": "1.0.0",
        "task": "binary_classification",
        "classes": ["healthy", "defective"],
        "class_mapping": {
            "healthy": "healthy=True AND no defect flags",
            "defective": "any of damage/rot/sprout=True",
        },
        "source_annotations": {
            "annotator_id": ANNOTATOR_ID,
            "annotator_count": 1,
            "total_pilot_records": 100,
            "inter_annotator_agreement": "NOT_AVAILABLE",
        },
        "samples": {
            "total_usable": total_usable,
            "excluded": len(excluded_samples),
            "excluded_details": excluded_samples,
        },
        "split": {
            "method": "stratified_random",
            "seed": RANDOM_SEED,
            "val_ratio": VAL_RATIO,
            "train_healthy": len(train_healthy),
            "train_defective": len(train_defective),
            "train_total": len(train_healthy) + len(train_defective),
            "val_healthy": len(val_healthy),
            "val_defective": len(val_defective),
            "val_total": len(val_healthy) + len(val_defective),
        },
        "defect_granularity_in_defective_class": {
            "damage_count": sum(1 for s in defective_samples if s["defects"]["damage"]),
            "rot_count": sum(1 for s in defective_samples if s["defects"]["rot"]),
            "sprout_count": sum(1 for s in defective_samples if s["defects"]["sprout"]),
            "note": "Multi-label detail preserved for future multi-class experiments",
        },
        "limitations": [
            "Only 99 usable samples (extremely small for deep learning)",
            "Single annotator — no IAA validation",
            "Binary classification loses multi-label granularity",
            "pilot_025 excluded (uncertain-only, no label)",
            "Undersized NOT modeled (no physical calibration)",
            "Heavy augmentation and transfer learning required to mitigate small dataset",
        ],
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }

    meta_path = os.path.join(OUTPUT_DIR, "dataset_meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print(f"[5/5] ✅ Generated dataset_meta.json")

    print(f"\n{'=' * 70}")
    print(f"PHASE 2 COMPLETE")
    print(f"  Dataset: {OUTPUT_DIR}")
    print(f"  Classes: healthy / defective (binary)")
    print(f"  Train:   {train_count} images")
    print(f"  Val:     {val_count} images")
    print(f"  Usable:  {total_usable} / 100 pilot images")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
