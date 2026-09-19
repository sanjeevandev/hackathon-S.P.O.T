#!/usr/bin/env python3
"""Phase 13 Real Human Annotation Pilot Execution & Inspection Script.

Manages human annotation queue, 10-image pilot review batching, multi-label schema
validation, and status calculation for the S.P.O.T. 100-image pilot dataset.
"""

import os
import sys
import json
import time
import datetime
from pathlib import Path
from backend.ai.annotation.workstation import AnnotationWorkstationManager

PROJECT_ROOT = Path(__file__).resolve().parent
DOCS_DIR = PROJECT_ROOT / "docs"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts" / "ml" / "defect_annotations"

os.makedirs(DOCS_DIR, exist_ok=True)
os.makedirs(ARTIFACTS_DIR, exist_ok=True)

start_time = time.time()
print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Step 1: Initializing Annotation Workstation Manager...")

manager = AnnotationWorkstationManager()

# Load 10-image pilot batch for inspection
pilot_10 = manager.get_pilot_10_batch("HUMAN_ANNOTATOR_01")
print(f"Loaded 10-image pilot batch for initial review: {len(pilot_10)} images.")

# Compute Phase 13 Status
status = manager.get_phase_13_status()

# Save status JSON artifact
status_path = ARTIFACTS_DIR / "phase_13_status.json"
with open(status_path, "w", encoding="utf-8") as f:
    json.dump(status, f, indent=2)

# Generate docs/PHASE_13_HUMAN_ANNOTATION.md
doc_content = f"""# S.P.O.T. Phase 13 — Real Human Annotation Pilot Status

## 1. Executive Summary
Phase 13 manages the **real human multi-label defect annotation process** on the 100-image pilot dataset selected during Phase 12A.

- **No Automated / ResNet18 / YOLO26 Labeling**: All ground truth annotations are recorded by human annotators.
- **Multi-Label Schema**: Healthy, Damaged, Rotten, Sprouted, Undersized, Uncertain.
- **Physical Size Rule**: `Undersized = UNAVAILABLE` unless calibrated physical measurement reference is available.
- **Pilot First Strategy**: Initial 10-image batch review before full 100-image completion.
- **Double Annotation**: Independent labeling by Annotator A & Annotator B without label copying.

---

## 2. Current Annotation Metrics

| Metric | Value |
| :--- | :--- |
| **Total Pilot Images** | {status['total_pilot']} |
| **Human Annotations Completed** | {status['human_annotations_completed']} |
| **Remaining Images** | {status['remaining']} |
| **Needs Review** | {status['needs_review']} |
| **Adjudicated** | {status['adjudicated']} |
| **Damage Count** | {status['damage']} |
| **Rot Count** | {status['rot']} |
| **Sprout Count** | {status['sprout']} |
| **Undersized Count** | {status['undersized']} |
| **Uncertain Count** | {status['uncertain']} |

---

## 3. Workstation Architecture & Status Lifecycle
```
[UNLABELED] -> (Annotator Input) -> [IN_PROGRESS] -> (Submit) -> [COMPLETE]
                                                         |
                                                  (Validation Error)
                                                         v
                                                  [NEEDS_REVIEW] -> (Adjudication) -> [ADJUDICATED]
```
"""

doc_path = DOCS_DIR / "PHASE_13_HUMAN_ANNOTATION.md"
with open(doc_path, "w", encoding="utf-8") as f:
    f.write(doc_content)

print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Saved status artifact to {status_path}")
print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Saved documentation to {doc_path}")
print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Phase 13 execution complete in {time.time()-start_time:.2f}s!")
