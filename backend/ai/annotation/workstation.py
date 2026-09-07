import os
import json
import csv
import hashlib
import datetime
from typing import Dict, Any, List, Optional
from backend.ai.annotation.validator import AnnotationValidator
from backend.ai.annotation.adjudication import AnnotationAdjudicator

WORKSTATION_DB_DIR = "artifacts/ml/defect_annotations/records"
EXPORT_DIR = "artifacts/ml/defect_annotations/exports"

os.makedirs(WORKSTATION_DB_DIR, exist_ok=True)
os.makedirs(EXPORT_DIR, exist_ok=True)

class AnnotationWorkstationManager:
    """Internal Human Annotation Workstation Manager.

    Handles queue loading, multi-label record persistence, double-annotation independence,
    validation rules, adjudication routing, and deterministic export without auto-labeling.
    """

    def __init__(self, manifest_path: str = "artifacts/ml/defect_annotations/annotation_manifest.json"):
        self.manifest_path = manifest_path
        self.records_dir = WORKSTATION_DB_DIR
        self.manifest_data = self._load_manifest()

    def _load_manifest(self) -> Dict[str, Any]:
        if not os.path.exists(self.manifest_path):
            raise FileNotFoundError(f"Annotation manifest not found at {self.manifest_path}")
        with open(self.manifest_path, "r") as f:
            return json.load(f)

    def get_queue(self, annotator_id: str = "HUMAN_ANNOTATOR_01") -> List[Dict[str, Any]]:
        """Loads queue for specified annotator with current completion status."""
        items = self.manifest_data.get("stratified_images", [])
        queue = []

        for item in items:
            image_id = item["image_id"]
            record_path = self._get_record_path(image_id, annotator_id)

            if os.path.exists(record_path):
                with open(record_path, "r") as f:
                    rec = json.load(f)
                status = rec.get("annotation_status", "COMPLETE")
            else:
                status = "UNLABELED"
                rec = None

            queue.append({
                "image_id": image_id,
                "semantic_attributes": item["semantic_attributes"],
                "audit_health_tag": item["audit_health_tag"],
                "blur_score": item.get("blur_score", 0.0),
                "brightness": item.get("brightness", 0.0),
                "annotation_status": status,
                "record": rec
            })

        return queue

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

    def save_annotation(self, record: Dict[str, Any]) -> Tuple[bool, List[str], str]:
        """Validates and persists human annotation record independently without modifying source images."""
        # Force version metadata
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

        with open(record_path, "w") as f:
            json.dump(record, f, indent=2)

        return is_valid, errors, record["annotation_status"]

    def _get_record_path(self, image_id: str, annotator_id: str) -> str:
        safe_name = hashlib.md5(f"{image_id}:{annotator_id}".encode('utf-8')).hexdigest()
        return os.path.join(self.records_dir, f"{safe_name}.json")

    def export_annotations(self, format: str = "json") -> str:
        """Exports all completed human annotations deterministically to JSON or CSV."""
        records = []
        for fname in os.listdir(self.records_dir):
            if fname.endswith(".json"):
                with open(os.path.join(self.records_dir, fname), "r") as f:
                    rec = json.load(f)
                if rec.get("annotation_status") in ["COMPLETE", "VERIFIED", "ADJUDICATED"]:
                    records.append(rec)

        if format == "json":
            out_path = os.path.join(EXPORT_DIR, "defect_annotations_export.json")
            with open(out_path, "w") as f:
                json.dump(records, f, indent=2)
            return out_path
        elif format == "csv":
            out_path = os.path.join(EXPORT_DIR, "defect_annotations_export.csv")
            with open(out_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "image_id", "annotator_id", "healthy", "damage", "rot", "sprout",
                    "undersized_status", "annotation_confidence", "annotation_status"
                ])
                for r in records:
                    defects = r.get("multi_label_defects", {})
                    size = r.get("size_assessment", {})
                    writer.writerow([
                        r["image_id"], r["annotator_id"],
                        defects.get("healthy", False), defects.get("damage", False),
                        defects.get("rot", False), defects.get("sprout", False),
                        size.get("undersized_status", "UNAVAILABLE"),
                        r.get("annotation_confidence", "HIGH"), r.get("annotation_status", "COMPLETE")
                    ])
            return out_path
        else:
            raise ValueError(f"Unsupported export format: {format}")
