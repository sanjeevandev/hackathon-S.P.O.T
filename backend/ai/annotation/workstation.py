import os
import json
import csv
import hashlib
import datetime
from typing import Dict, Any, List, Optional, Tuple
from backend.ai.annotation.validator import AnnotationValidator
from backend.ai.annotation.adjudication import AnnotationAdjudicator

WORKSTATION_DB_DIR = "artifacts/ml/defect_annotations/records"
EXPORT_DIR = "artifacts/ml/defect_annotations/exports"
DEFAULT_PILOT_CSV = "artifacts/ml/defect_annotations/pilot_100/manifest.csv"
DEFAULT_MANIFEST_JSON = "artifacts/ml/defect_annotations/annotation_manifest.json"

os.makedirs(WORKSTATION_DB_DIR, exist_ok=True)
os.makedirs(EXPORT_DIR, exist_ok=True)


class AnnotationWorkstationManager:
    """Internal Human Annotation Workstation Manager for S.P.O.T.

    Handles queue loading from pilot manifests, multi-label record persistence,
    double-annotation independence, quality validation rules, 10-image pilot batching,
    adjudication routing, and deterministic export without auto-labeling.
    """

    def __init__(
        self,
        manifest_path: Optional[str] = None,
        records_dir: str = WORKSTATION_DB_DIR
    ):
        if manifest_path is None:
            if os.path.exists(DEFAULT_PILOT_CSV):
                manifest_path = DEFAULT_PILOT_CSV
            elif os.path.exists(DEFAULT_MANIFEST_JSON):
                manifest_path = DEFAULT_MANIFEST_JSON
            else:
                manifest_path = DEFAULT_PILOT_CSV

        self.manifest_path = manifest_path
        self.records_dir = records_dir
        os.makedirs(self.records_dir, exist_ok=True)
        self.items = self._load_manifest()

    def _load_manifest(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.manifest_path):
            return []

        items = []
        if self.manifest_path.endswith(".csv"):
            with open(self.manifest_path, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    items.append({
                        "image_id": row.get("image_id", row.get("destination_filename", "")),
                        "source_path": row.get("source_path", ""),
                        "destination_filename": row.get("destination_filename", ""),
                        "semantic_attributes": {
                            "organ": "BULB",
                            "color": row.get("onion_color", "UNKNOWN"),
                            "arrangement": row.get("arrangement", "UNKNOWN")
                        },
                        "audit_health_tag": row.get("existing_health_label", "UNKNOWN"),
                        "capture_cluster": row.get("capture_cluster", "NONE"),
                        "duplicate_group": row.get("duplicate_group", "NONE")
                    })
        elif self.manifest_path.endswith(".json"):
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                raw_items = data.get("stratified_images", data.get("images", []))
                for item in raw_items:
                    items.append({
                        "image_id": item["image_id"],
                        "source_path": item.get("source_path", ""),
                        "destination_filename": item.get("destination_filename", item["image_id"]),
                        "semantic_attributes": item.get("semantic_attributes", {}),
                        "audit_health_tag": item.get("audit_health_tag", "UNKNOWN"),
                        "blur_score": item.get("blur_score", 0.0),
                        "brightness": item.get("brightness", 0.0)
                    })
        return items

    def get_queue(self, annotator_id: str = "HUMAN_ANNOTATOR_01") -> List[Dict[str, Any]]:
        """Loads queue for specified annotator with current completion status."""
        queue = []
        for item in self.items:
            image_id = item["image_id"]
            record_path = self._get_record_path(image_id, annotator_id)

            if os.path.exists(record_path):
                with open(record_path, "r", encoding="utf-8") as f:
                    rec = json.load(f)
                status = rec.get("annotation_status", "COMPLETE")
            else:
                status = "UNLABELED"
                rec = None

            queue.append({
                "image_id": image_id,
                "source_path": item.get("source_path", ""),
                "destination_filename": item.get("destination_filename", ""),
                "semantic_attributes": item.get("semantic_attributes", {}),
                "audit_health_tag": item.get("audit_health_tag", "UNKNOWN"),
                "annotation_status": status,
                "record": rec
            })
        return queue

    def get_pilot_10_batch(self, annotator_id: str = "HUMAN_ANNOTATOR_01") -> List[Dict[str, Any]]:
        """Returns the first 10 items for pilot review (Pause -> Inspect -> Resume)."""
        full_queue = self.get_queue(annotator_id)
        return full_queue[:10]

    def get_progress(self, annotator_id: str = "HUMAN_ANNOTATOR_01") -> Dict[str, Any]:
        """Calculates progress metrics for specified annotator."""
        queue = self.get_queue(annotator_id)
        total = len(queue)
        completed = sum(1 for item in queue if item["annotation_status"] in ["COMPLETE", "VERIFIED", "ADJUDICATED"])
        needs_review = sum(1 for item in queue if item["annotation_status"] == "NEEDS_REVIEW")
        adjudicated = sum(1 for item in queue if item["annotation_status"] == "ADJUDICATED")
        remaining = total - completed - needs_review

        return {
            "annotator_id": annotator_id,
            "total_images": total,
            "completed": completed,
            "remaining": remaining,
            "needs_review": needs_review,
            "adjudicated": adjudicated,
            "completion_percentage": round((completed / total) * 100, 2) if total > 0 else 0.0
        }

    def get_phase_13_status(self) -> Dict[str, Any]:
        """Calculates aggregate Phase 13 pilot status across real human annotations."""
        total_pilot = len(self.items) if self.items else 100
        pilot_image_ids = {item["image_id"] for item in self.items} if self.items else set()

        completed = 0
        needs_review = 0
        adjudicated = 0
        
        damage_count = 0
        rot_count = 0
        sprout_count = 0
        undersized_count = 0
        uncertain_count = 0

        # Scan records_dir for real human records matching pilot images
        if os.path.exists(self.records_dir):
            for fname in os.listdir(self.records_dir):
                if fname.endswith(".json"):
                    record_path = os.path.join(self.records_dir, fname)
                    try:
                        with open(record_path, "r", encoding="utf-8") as f:
                            rec = json.load(f)
                    except Exception:
                        continue

                    # Filter out synthetic test suite entries or entries not in pilot
                    annotator = rec.get("annotator_id", "")
                    if "TEST" in annotator:
                        continue
                    if pilot_image_ids and rec.get("image_id") not in pilot_image_ids:
                        continue

                    status = rec.get("annotation_status", "UNLABELED")
                    if status in ["COMPLETE", "VERIFIED"]:
                        completed += 1
                    elif status == "ADJUDICATED":
                        adjudicated += 1
                    elif status == "NEEDS_REVIEW":
                        needs_review += 1

                    if status in ["COMPLETE", "VERIFIED", "ADJUDICATED"]:
                        defects = rec.get("multi_label_defects", {})
                        if defects.get("damage", False):
                            damage_count += 1
                        if defects.get("rot", False):
                            rot_count += 1
                        if defects.get("sprout", False):
                            sprout_count += 1
                        if defects.get("uncertain", False) or rec.get("annotation_confidence") == "LOW":
                            uncertain_count += 1
                            
                        size_assessment = rec.get("size_assessment", {})
                        if size_assessment.get("undersized_status") == "UNDERSIZED":
                            undersized_count += 1

        remaining = total_pilot - completed - needs_review - adjudicated

        return {
            "total_pilot": total_pilot,
            "human_annotations_completed": completed,
            "remaining": max(0, remaining),
            "needs_review": needs_review,
            "adjudicated": adjudicated,
            "damage": damage_count,
            "rot": rot_count,
            "sprout": sprout_count,
            "undersized": undersized_count,
            "uncertain": uncertain_count
        }


    def save_annotation(self, record: Dict[str, Any]) -> Tuple[bool, List[str], str]:
        """Validates and persists human annotation record independently without modifying source images."""
        record["dataset_version"] = "1.0.0-audited"
        record["defect_dataset_version"] = "0.1.0"
        record["annotation_version"] = "0.1.0"
        record["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        if "created_at" not in record:
            record["created_at"] = record["updated_at"]

        # Run validation
        is_valid, errors, review_status = AnnotationValidator.validate_record(record)
        record["review_status"] = review_status
        record["annotation_status"] = "NEEDS_REVIEW" if review_status == "NEEDS_REVIEW" else "COMPLETE"

        # Save record
        image_id = record["image_id"]
        annotator_id = record["annotator_id"]
        record_path = self._get_record_path(image_id, annotator_id)

        with open(record_path, "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2)

        return is_valid, errors, record["annotation_status"]

    def _get_record_path(self, image_id: str, annotator_id: str) -> str:
        safe_name = hashlib.md5(f"{image_id}:{annotator_id}".encode('utf-8')).hexdigest()
        return os.path.join(self.records_dir, f"{safe_name}.json")

    def export_annotations(self, format: str = "json") -> str:
        """Exports all completed human annotations deterministically to JSON or CSV."""
        records = []
        if os.path.exists(self.records_dir):
            for fname in os.listdir(self.records_dir):
                if fname.endswith(".json"):
                    with open(os.path.join(self.records_dir, fname), "r", encoding="utf-8") as f:
                        rec = json.load(f)
                    annotator = rec.get("annotator_id", "")
                    if "TEST" in annotator:
                        continue
                    if rec.get("annotation_status") in ["COMPLETE", "VERIFIED", "ADJUDICATED"]:
                        records.append(rec)

        if format == "json":
            out_path = os.path.join(EXPORT_DIR, "defect_annotations_export.json")
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=2)
            return out_path
        elif format == "csv":
            out_path = os.path.join(EXPORT_DIR, "defect_annotations_export.csv")
            with open(out_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "image_id", "annotator_id", "healthy", "damage", "rot", "sprout", "uncertain",
                    "undersized_status", "annotation_confidence", "annotation_status"
                ])
                for r in records:
                    defects = r.get("multi_label_defects", {})
                    size = r.get("size_assessment", {})
                    writer.writerow([
                        r["image_id"], r["annotator_id"],
                        defects.get("healthy", False), defects.get("damage", False),
                        defects.get("rot", False), defects.get("sprout", False), defects.get("uncertain", False),
                        size.get("undersized_status", "UNAVAILABLE"),
                        r.get("annotation_confidence", "HIGH"), r.get("annotation_status", "COMPLETE")
                    ])
            return out_path
        else:
            raise ValueError(f"Unsupported export format: {format}")
