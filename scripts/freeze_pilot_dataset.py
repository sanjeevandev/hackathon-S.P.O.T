"""
S.P.O.T. Phase 1 — Freeze Pilot Dataset
========================================
Creates a versioned, checksummed snapshot of the 100 HUMAN_ANNOTATOR_A
pilot annotations WITHOUT modifying the original records.

Output: artifacts/ml/pilot_v1.0.0_single_annotator/
"""

import csv
import datetime
import hashlib
import json
import os
import shutil
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RECORDS_DIR = os.path.join(PROJECT_ROOT, "artifacts", "ml", "defect_annotations", "records")
PILOT_IMAGES_DIR = os.path.join(PROJECT_ROOT, "artifacts", "ml", "defect_annotations", "pilot_100", "images")
SNAPSHOT_DIR = os.path.join(PROJECT_ROOT, "artifacts", "ml", "pilot_v1.0.0_single_annotator")

DATASET_VERSION = "1.0.0-pilot-single-annotator"
ANNOTATOR_ID = "HUMAN_ANNOTATOR_A"
EXPECTED_COUNT = 100


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main():
    print("=" * 70)
    print("S.P.O.T. Phase 1 — Freeze Pilot Dataset")
    print("=" * 70)

    # ---- Step 1: Load and filter HUMAN_ANNOTATOR_A records ----
    all_records = []
    for fname in sorted(os.listdir(RECORDS_DIR)):
        if not fname.endswith(".json"):
            continue
        fpath = os.path.join(RECORDS_DIR, fname)
        with open(fpath, "r", encoding="utf-8") as f:
            rec = json.load(f)
        if rec.get("annotator_id") == ANNOTATOR_ID:
            rec["_source_file"] = fname
            rec["_source_path"] = fpath
            all_records.append(rec)

    print(f"\n[1/5] Found {len(all_records)} {ANNOTATOR_ID} records")

    if len(all_records) != EXPECTED_COUNT:
        print(f"  ❌ FAIL: Expected {EXPECTED_COUNT}, found {len(all_records)}")
        sys.exit(1)
    print(f"  ✅ PASS: Exactly {EXPECTED_COUNT} records confirmed")

    # ---- Step 2: Verify pilot_001–pilot_100 coverage ----
    image_ids = sorted([r["image_id"] for r in all_records])
    expected_ids = [f"pilot_{i:03d}" for i in range(1, 101)]

    missing = set(expected_ids) - set(image_ids)
    extra = set(image_ids) - set(expected_ids)

    if missing:
        print(f"  ❌ FAIL: Missing pilot IDs: {sorted(missing)}")
        sys.exit(1)
    if extra:
        print(f"  ⚠️  Extra IDs (not pilot_NNN): {sorted(extra)}")

    print(f"[2/5] ✅ PASS: pilot_001 through pilot_100 — full coverage confirmed")

    # ---- Step 3: Verify all statuses are COMPLETE ----
    statuses = set(r.get("annotation_status") for r in all_records)
    if statuses != {"COMPLETE"}:
        print(f"  ❌ FAIL: Non-COMPLETE statuses found: {statuses}")
        sys.exit(1)
    print(f"[3/5] ✅ PASS: All 100 records have annotation_status=COMPLETE")

    # ---- Step 4: Create versioned snapshot ----
    annotations_dir = os.path.join(SNAPSHOT_DIR, "annotations")
    os.makedirs(annotations_dir, exist_ok=True)

    record_checksums = {}
    for rec in all_records:
        source_file = rec["_source_file"]
        source_path = rec["_source_path"]

        # Copy the original JSON file as-is (read-only snapshot)
        dest_path = os.path.join(annotations_dir, source_file)
        shutil.copy2(source_path, dest_path)

        record_checksums[source_file] = sha256_file(source_path)

    print(f"[4/5] ✅ Copied {len(record_checksums)} annotation files to snapshot")

    # ---- Step 5: Generate snapshot metadata and labels CSV ----

    # Labels summary CSV
    csv_path = os.path.join(SNAPSHOT_DIR, "labels_summary.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as csvf:
        writer = csv.writer(csvf)
        writer.writerow([
            "image_id", "healthy", "damage", "rot", "sprout", "uncertain",
            "annotation_confidence", "organ", "color", "arrangement"
        ])
        for rec in sorted(all_records, key=lambda r: r["image_id"]):
            defects = rec.get("multi_label_defects", {})
            sem = rec.get("semantic_attributes", {})
            writer.writerow([
                rec["image_id"],
                defects.get("healthy", False),
                defects.get("damage", False),
                defects.get("rot", False),
                defects.get("sprout", False),
                defects.get("uncertain", False),
                rec.get("annotation_confidence", ""),
                sem.get("organ", ""),
                sem.get("color", ""),
                sem.get("arrangement", ""),
            ])

    # Count label distribution
    healthy_count = sum(1 for r in all_records
                        if r.get("multi_label_defects", {}).get("healthy", False)
                        and not any(r.get("multi_label_defects", {}).get(d, False)
                                    for d in ["damage", "rot", "sprout"]))
    defect_count = sum(1 for r in all_records
                       if any(r.get("multi_label_defects", {}).get(d, False)
                              for d in ["damage", "rot", "sprout"]))
    uncertain_only = sum(1 for r in all_records
                         if not r.get("multi_label_defects", {}).get("healthy", False)
                         and not any(r.get("multi_label_defects", {}).get(d, False)
                                     for d in ["damage", "rot", "sprout"]))

    # Snapshot metadata
    meta = {
        "dataset_version": DATASET_VERSION,
        "dataset_type": "SINGLE-ANNOTATOR PILOT DATA",
        "annotator_id": ANNOTATOR_ID,
        "annotator_count": 1,
        "inter_annotator_agreement": "NOT_AVAILABLE — single annotator only",
        "total_records": len(all_records),
        "pilot_id_range": "pilot_001 → pilot_100",
        "all_statuses_complete": True,
        "label_distribution": {
            "pure_healthy": healthy_count,
            "any_defect": defect_count,
            "uncertain_only": uncertain_only,
        },
        "defect_breakdown": {
            "damage": sum(1 for r in all_records if r.get("multi_label_defects", {}).get("damage", False)),
            "rot": sum(1 for r in all_records if r.get("multi_label_defects", {}).get("rot", False)),
            "sprout": sum(1 for r in all_records if r.get("multi_label_defects", {}).get("sprout", False)),
        },
        "confidence_distribution": {
            "HIGH": sum(1 for r in all_records if r.get("annotation_confidence") == "HIGH"),
            "MEDIUM": sum(1 for r in all_records if r.get("annotation_confidence") == "MEDIUM"),
            "LOW": sum(1 for r in all_records if r.get("annotation_confidence") == "LOW"),
        },
        "source_records_dir": RECORDS_DIR,
        "snapshot_created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "record_checksums": record_checksums,
        "notes": [
            "This is a SINGLE-ANNOTATOR dataset. No inter-annotator agreement (IAA) metrics are claimed.",
            "HUMAN_ANNOTATOR_B data was not persisted and cannot be recovered.",
            "The 'uncertain' flag is orthogonal to defect labels — it indicates annotator uncertainty.",
            "pilot_025 has uncertain=True with no healthy/defect labels set.",
            "Undersized is NOT a learned class (no physical calibration available).",
        ]
    }

    meta_path = os.path.join(SNAPSHOT_DIR, "snapshot_meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print(f"[5/5] ✅ Generated snapshot_meta.json and labels_summary.csv")

    print(f"\n{'=' * 70}")
    print(f"PHASE 1 COMPLETE")
    print(f"  Snapshot: {SNAPSHOT_DIR}")
    print(f"  Version:  {DATASET_VERSION}")
    print(f"  Records:  {len(all_records)}")
    print(f"  Healthy:  {healthy_count} | Defective: {defect_count} | Uncertain-only: {uncertain_only}")
    print(f"  Type:     SINGLE-ANNOTATOR PILOT DATA")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
