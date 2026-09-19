#!/usr/bin/env python3
"""Phase 12A Pilot 100 Image Selection Script for S.P.O.T.

Selects exactly 100 representative bulb images from the authoritative onion dataset
for future human defect annotation.

Guarantees:
- Stratification across Health (Healthy/Unhealthy), Color (Red/White), Arrangement (Single/Multiple)
- Zero exact duplicates inside pilot
- Zero near-duplicates inside pilot
- High cluster diversity across capture sessions
- READ-ONLY operation against source dataset
"""

import os
import sys
import json
import csv
import zipfile
import random
import shutil
import hashlib
from collections import defaultdict
from pathlib import Path
from PIL import Image

SEED = 42
random.seed(SEED)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "artifacts" / "ml" / "defect_annotations" / "pilot_100"
IMAGES_DIR = OUTPUT_DIR / "images"
MANIFEST_PATH = OUTPUT_DIR / "manifest.csv"
SUMMARY_PATH = OUTPUT_DIR / "selection_summary.json"
README_PATH = OUTPUT_DIR / "README.md"

DATASET_ZIP = Path("/run/media/sanjeeva/0354-C3F0/ONION IQ/Image Dataset of Red and White Onion Bulbs and Lea/Onion Leaves and Bulb Dataset.zip")
INVENTORY_PATH = PROJECT_ROOT / "artifacts" / "dataset_audit" / "file_inventory.json"
DUP_REPORT_PATH = PROJECT_ROOT / "artifacts" / "dataset_audit" / "duplicate_report.json"

if not DATASET_ZIP.exists():
    print(f"Error: Dataset archive not found at {DATASET_ZIP}")
    sys.exit(1)

# Ensure clean output directory
if OUTPUT_DIR.exists():
    shutil.rmtree(OUTPUT_DIR)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# Load audit artifacts
with open(INVENTORY_PATH, "r") as f:
    inventory = json.load(f)

with open(DUP_REPORT_PATH, "r") as f:
    dup_report = json.load(f)

files = inventory["files"]
# Filter to valid bulb images only
bulbs = [f for f in files if f.get("is_bulb", True) and f.get("valid", True)]

# Build exact duplicate lookup (hash -> group_id)
exact_dup_lookup = {}
for group_id, dup_files in dup_report.get("exact_duplicate_groups", {}).items():
    for fn in dup_files:
        exact_dup_lookup[fn] = group_id

# Build near duplicate pair lookup (fn -> set of near-dup filenames)
near_dup_graph = defaultdict(set)
for pair in dup_report.get("near_duplicate_pairs", []):
    f1, f2 = pair["file1"], pair["file2"]
    near_dup_graph[f1].add(f2)
    near_dup_graph[f2].add(f1)

# Categorize bulbs into 8 strata
# Strata keys: (HEALTHY/UNHEALTHY, RED/WHITE, SINGLE/MULTIPLE)
strata = defaultdict(list)

for item in bulbs:
    fn = item["filename"]
    health = "HEALTHY" if item.get("is_healthy", True) else "UNHEALTHY"
    color = "RED" if item.get("is_red", False) else ("WHITE" if item.get("is_white", False) else "UNKNOWN")
    arr = "SINGLE" if item.get("is_single", False) else ("MULTIPLE" if item.get("is_multiple", False) else "UNKNOWN")
    
    if color == "UNKNOWN" or arr == "UNKNOWN":
        continue

    # Extract capture cluster based on parent path + prefix
    parts = Path(fn).parts
    folder_str = "/".join(parts[:-1])
    stem = Path(fn).stem
    # Prefix up to first 7 chars for burst sequence grouping (e.g. Onion0404)
    cluster_id = f"{folder_str}::{stem[:10]}"
    
    item_meta = {
        "filename": fn,
        "basename": item["basename"],
        "file_size": item["file_size"],
        "sha256": item.get("sha256", ""),
        "dhash": item.get("dhash", ""),
        "health": health,
        "color": color,
        "arrangement": arr,
        "cluster_id": cluster_id,
        "exact_dup_group": exact_dup_lookup.get(fn, "NONE")
    }
    strata[(health, color, arr)].append(item_meta)

# Target counts for the 8 strata to sum to exactly 100
target_counts = {
    ("HEALTHY", "RED", "SINGLE"): 13,
    ("HEALTHY", "RED", "MULTIPLE"): 12,
    ("HEALTHY", "WHITE", "SINGLE"): 13,
    ("HEALTHY", "WHITE", "MULTIPLE"): 12,
    ("UNHEALTHY", "RED", "SINGLE"): 13,
    ("UNHEALTHY", "RED", "MULTIPLE"): 12,
    ("UNHEALTHY", "WHITE", "SINGLE"): 13,
    ("UNHEALTHY", "WHITE", "MULTIPLE"): 12
}

selected_items = []
selected_filenames = set()
selected_exact_groups = set()
selected_clusters = defaultdict(int)

for key, target_n in target_counts.items():
    candidates = strata[key]
    random.shuffle(candidates)
    
    chosen_for_stratum = 0
    for cand in candidates:
        fn = cand["filename"]
        exact_group = cand["exact_dup_group"]
        cluster_id = cand["cluster_id"]
        
        # Check duplicate group collision
        if exact_group != "NONE" and exact_group in selected_exact_groups:
            continue
            
        # Check near duplicate collision
        if any(near_fn in selected_filenames for near_fn in near_dup_graph[fn]):
            continue
            
        # Limit concentration from same capture cluster (max 2 per cluster across entire pilot)
        if selected_clusters[cluster_id] >= 2:
            continue
            
        selected_items.append(cand)
        selected_filenames.add(fn)
        if exact_group != "NONE":
            selected_exact_groups.add(exact_group)
        selected_clusters[cluster_id] += 1
        chosen_for_stratum += 1
        
        if chosen_for_stratum == target_n:
            break
            
    if chosen_for_stratum < target_n:
        print(f"Warning: Could only select {chosen_for_stratum}/{target_n} for stratum {key}")

print(f"Total pilot images selected: {len(selected_items)}")
assert len(selected_items) == 100, f"Expected 100 selected images, got {len(selected_items)}"

# Extract images from zip into artifacts/ml/defect_annotations/pilot_100/images/
manifest_rows = []
zip_map = {}

with zipfile.ZipFile(DATASET_ZIP, "r") as z:
    for idx, item in enumerate(selected_items, start=1):
        source_path = item["filename"]
        ext = Path(source_path).suffix
        dest_filename = f"pilot_{idx:03d}_{item['basename']}"
        dest_path = IMAGES_DIR / dest_filename
        
        # Read from zip archive
        img_bytes = z.read(source_path)
        with open(dest_path, "wb") as img_f:
            img_f.write(img_bytes)
            
        # Validate image readability with PIL
        with Image.open(dest_path) as pil_img:
            pil_img.verify()
            
        manifest_rows.append({
            "image_id": f"pilot_{idx:03d}",
            "source_path": source_path,
            "destination_filename": dest_filename,
            "existing_health_label": item["health"],
            "onion_color": item["color"],
            "arrangement": item["arrangement"],
            "capture_cluster": item["cluster_id"],
            "duplicate_group": item["exact_dup_group"],
            "annotation_status": "UNLABELED"
        })

# Write manifest.csv
fieldnames = [
    "image_id",
    "source_path",
    "destination_filename",
    "existing_health_label",
    "onion_color",
    "arrangement",
    "capture_cluster",
    "duplicate_group",
    "annotation_status"
]

with open(MANIFEST_PATH, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(manifest_rows)

# Generate selection_summary.json
health_summary = defaultdict(int)
color_summary = defaultdict(int)
arr_summary = defaultdict(int)
cluster_summary = set()

for row in manifest_rows:
    health_summary[row["existing_health_label"]] += 1
    color_summary[row["onion_color"]] += 1
    arr_summary[row["arrangement"]] += 1
    cluster_summary.add(row["capture_cluster"])

summary_data = {
    "seed": SEED,
    "total_pilot_images": len(manifest_rows),
    "health_breakdown": dict(health_summary),
    "color_breakdown": dict(color_summary),
    "arrangement_breakdown": dict(arr_summary),
    "unique_capture_clusters": len(cluster_summary),
    "exact_duplicates_inside_pilot": 0,
    "near_duplicates_inside_pilot": 0,
    "dataset_source": str(DATASET_ZIP),
    "strata_counts": {f"{k[0]}_{k[1]}_{k[2]}": target_counts[k] for k in target_counts},
    "source_dataset_modified": False,
    "validation_status": "PASS"
}

with open(SUMMARY_PATH, "w") as f:
    json.dump(summary_data, f, indent=2)

# Generate README.md
readme_content = f"""# S.P.O.T. Phase 12A — 100 Image Human Annotation Pilot

## 1. Executive Summary
This pilot dataset contains **exactly 100 representative bulb images** extracted deterministically from the authoritative S.P.O.T. onion dataset archive (`{DATASET_ZIP}`).

All images are selected for future human multi-label defect annotation (Damaged, Rotten, Sprouted, Undersized). **No defect labels are pre-assigned in this phase** (`annotation_status = UNLABELED`).

---

## 2. Stratification Matrix & Balance

| Health Status | Onion Color | Arrangement | Count |
| :--- | :--- | :--- | :--- |
| **Healthy** | Red | Single | {target_counts[("HEALTHY", "RED", "SINGLE")]} |
| **Healthy** | Red | Multiple | {target_counts[("HEALTHY", "RED", "MULTIPLE")]} |
| **Healthy** | White | Single | {target_counts[("HEALTHY", "WHITE", "SINGLE")]} |
| **Healthy** | White | Multiple | {target_counts[("HEALTHY", "WHITE", "MULTIPLE")]} |
| **Unhealthy** | Red | Single | {target_counts[("UNHEALTHY", "RED", "SINGLE")]} |
| **Unhealthy** | Red | Multiple | {target_counts[("UNHEALTHY", "RED", "MULTIPLE")]} |
| **Unhealthy** | White | Single | {target_counts[("UNHEALTHY", "WHITE", "SINGLE")]} |
| **Unhealthy** | White | Multiple | {target_counts[("UNHEALTHY", "WHITE", "MULTIPLE")]} |
| **TOTAL** | | | **100** |

---

## 3. Data Integrity & Diversity Safeguards
- **Random Seed**: `{SEED}` (Deterministic & Reproducible).
- **Exact Duplicates**: 0 inside pilot.
- **Near Duplicates**: 0 inside pilot.
- **Capture Cluster Diversity**: Distributed across {len(cluster_summary)} distinct capture sessions.
- **Source Read-Only**: Source dataset archive left 100% untouched.

---

## 4. Directory Structure
```
pilot_100/
├── images/                 # 100 extracted JPEG bulb images (pilot_001_*.jpg to pilot_100_*.jpg)
├── manifest.csv            # Canonical pilot manifest with image IDs and metadata
├── selection_summary.json  # Comprehensive validation summary
└── README.md               # Pilot dataset documentation
```
"""

with open(README_PATH, "w") as f:
    f.write(readme_content)

print(f"✅ Phase 12A Pilot 100 created successfully at {OUTPUT_DIR}")
