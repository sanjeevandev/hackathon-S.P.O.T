"""
S.P.O.T. YOLO26 Classifier Vision Model
========================================
Implements the VisionModel interface using a trained YOLO26n-cls checkpoint
for binary onion quality classification (healthy / defective).

Source: real_model (NOT a mock — trained on real human-annotated pilot data)
"""

import os
import time
from typing import Literal, Optional

from backend.ai.base import VisionModel
from backend.ai.schemas import (
    ImageInput,
    VisionResult,
    OnionDetection,
    DefectProbabilities,
    SizeEstimate,
    EvidenceRegion,
)

# Resolve the best checkpoint path for YOLO26
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_DEFAULT_CHECKPOINT = os.path.join(
    _PROJECT_ROOT, "artifacts", "ml", "experiments",
    "yolo26n_cls_pilot_v1", "weights", "best.pt"
)


class YOLO26ClassifierModel(VisionModel):
    """Production-ready binary classifier using YOLO26n-cls trained on pilot data.

    Classifies whole onion images as healthy or defective.
    Does NOT fabricate bounding boxes, size estimates, or physical properties.
    """

    def __init__(self, checkpoint_path: Optional[str] = None):
        self._checkpoint_path = checkpoint_path or _DEFAULT_CHECKPOINT
        self._model = None
        self._class_names = None

    def _load_model(self):
        """Lazy-load the YOLO26 model on first inference."""
        if self._model is not None:
            return

        if not os.path.exists(self._checkpoint_path):
            raise FileNotFoundError(
                f"YOLO26 checkpoint not found at {self._checkpoint_path}. "
                "Run scripts/train_yolo26_cls.py first."
            )

        from ultralytics import YOLO
        self._model = YOLO(self._checkpoint_path)
        self._class_names = self._model.names  # {0: 'defective', 1: 'healthy'} or similar
        print(f"[YOLO26ClassifierModel] Loaded checkpoint: {self._checkpoint_path}")
        print(f"[YOLO26ClassifierModel] Classes: {self._class_names}")

    @property
    def model_name(self) -> str:
        return "YOLO26n-cls-pilot"

    @property
    def model_version(self) -> str:
        return "1.0.0-pilot"

    @property
    def source(self) -> Literal["development_mock", "real_model"]:
        return "real_model"

    def analyze(self, image_input: ImageInput, image_bytes: bytes) -> VisionResult:
        """Classify an onion image as healthy or defective.

        Maps the binary classification result into the existing VisionResult
        schema with DefectProbabilities. Since this is a classifier (not a
        detector), a single whole-image detection is created.
        """
        self._load_model()
        start_time = time.perf_counter()

        # Run inference — YOLO accepts raw bytes via PIL
        from PIL import Image
        import io

        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        results = self._model.predict(
            source=img,
            imgsz=224,
            device="cpu",
            verbose=False,
        )

        processing_time_ms = round((time.perf_counter() - start_time) * 1000.0, 3)

        if not results or len(results) == 0:
            return VisionResult(
                request_id=image_input.image_id,
                model_name=self.model_name,
                model_version=self.model_version,
                source=self.source,
                processing_time_ms=processing_time_ms,
                onions=[],
                overall_confidence=0.0,
                status="NO_VALID_DETECTIONS",
                error_message="YOLO26 returned no classification result",
            )

        # Extract classification probabilities
        probs = results[0].probs
        top1_idx = int(probs.top1)
        top1_conf = float(probs.top1conf)
        pred_class = self._class_names[top1_idx]

        # Map to defect probabilities
        all_probs = probs.data.tolist() if hasattr(probs.data, 'tolist') else list(probs.data)

        defective_prob = 0.0
        healthy_prob = 0.0
        for idx, name in self._class_names.items():
            if name == "defective":
                defective_prob = float(all_probs[idx])
            elif name == "healthy":
                healthy_prob = float(all_probs[idx])

        # Create a whole-image detection entry
        w, h = image_input.width, image_input.height
        detection = OnionDetection(
            onion_id=f"CLS-{image_input.image_id}",
            bbox=[0, 0, w, h],
            detection_confidence=top1_conf,
            defect_probabilities=DefectProbabilities(
                damage=round(defective_prob, 4),  # Binary: all defect probability mapped to damage
                rot=0.0,    # Cannot distinguish — binary classifier
                sprouting=0.0,  # Cannot distinguish — binary classifier
            ),
            size_estimate=SizeEstimate(
                status="UNAVAILABLE",
                estimated_diameter_mm=None,
                calibration_method=None,
                confidence=0.0,
            ),
            evidence_regions=[],
        )

        return VisionResult(
            request_id=image_input.image_id,
            model_name=self.model_name,
            model_version=self.model_version,
            source=self.source,
            processing_time_ms=processing_time_ms,
            onions=[detection],
            overall_confidence=round(top1_conf, 4),
            status="SUCCESS",
        )
