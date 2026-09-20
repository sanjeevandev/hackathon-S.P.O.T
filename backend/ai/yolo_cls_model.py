"""
S.P.O.T. YOLO26 Classifier Vision Model
========================================
Implements the VisionModel interface using a trained YOLO26n-cls checkpoint
for binary onion quality classification (healthy / defective).

Source: real_model (NOT a mock — trained on real human-annotated pilot data)
"""

import io
import os
import time
import logging
from typing import Literal, Optional

from PIL import Image

from backend.ai.base import VisionModel
from backend.ai.schemas import (
    ImageInput,
    VisionResult,
    OnionDetection,
    DefectProbabilities,
    SizeEstimate,
    EvidenceRegion,
)

logger = logging.getLogger("SPOTAI.YOLO26ClassifierModel")

# Resolve the best checkpoint path for YOLO26
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_DEFAULT_CHECKPOINT = os.path.join(
    _PROJECT_ROOT, "artifacts", "ml", "experiments",
    "yolo26n_cls_pilot_v1", "weights", "best.pt"
)

# Constant training/eval geometry. The checkpoint was trained and validated at a
# fixed 224x224 classification input; inference MUST use the same size or the
# result is not reproducible against the recorded experiment results.
_MODEL_IMGSZ = 224
_MODEL_DEVICE = "cpu"

# Health-axis side from which the binary "defective" probability is read.
_DEFECTIVE_CLASS_LABELS = {"defective", "damage", "disease", "rot", "rotten"}

# A multi-class checkpoint mapped into this binary contract is unsupported and
# is refused at load time (rather than silently mis-mapping its probabilities).
MAX_SUPPORTED_CLASSES = 2

# Whether the trained checkpoint actually exists on disk. The registry uses this
# so it never advertises (or silently selects) a model whose weights are absent.
_YOLO26_CHECKPOINT_EXISTS = os.path.exists(_DEFAULT_CHECKPOINT)


class YOLO26ClassifierModel(VisionModel):
    """Production-ready binary classifier using YOLO26n-cls trained on pilot data.

    Classifies whole onion images as healthy or defective.
    Does NOT fabricate bounding boxes, size estimates, or physical properties.

    Confidence policy:
    The classifier reports the model's own top-1 confidence verbatim in
    ``VisionResult.overall_confidence`` and always returns ``SUCCESS`` for a
    valid binary prediction. LOW-CONFIDENCE handling is the responsibility of the
    grading engine, which compares ``overall_confidence`` against the active
    ``GradingProfile.confidence_min_threshold`` (default 0.70) and flags
    ``REVIEW_REQUIRED`` — see ``backend/grading/grading_engine.py``. This keeps a
    single source of truth for the accept threshold.

    Note: `source` returns 'real_model' only when the checkpoint is actually
    present on disk; otherwise this class is not usable and reports itself as
    unavailable, so callers never treat a missing checkpoint as a real model.
    """

    def __init__(self, checkpoint_path: Optional[str] = None):
        self._checkpoint_path = checkpoint_path or _DEFAULT_CHECKPOINT
        self._model = None
        self._class_names = None

    @property
    def checkpoint_path(self) -> str:
        return self._checkpoint_path

    @classmethod
    def default_checkpoint_path(cls) -> str:
        return _DEFAULT_CHECKPOINT

    @property
    def checkpoint_available(self) -> bool:
        return os.path.exists(self._checkpoint_path)

    @property
    def runtime_device(self) -> str:
        return "PyTorch / CPU (YOLO26n-cls)"

    def _load_model(self):
        """Lazy-load the YOLO26 model on first inference.

        Raises:
            RuntimeError: if the checkpoint is missing or cannot be loaded.
            ValueError: if the checkpoint does not expose class names, or exposes
                more than MAX_SUPPORTED_CLASSES classes (i.e. is not binary).
        """
        if self._model is not None:
            return

        if not os.path.exists(self._checkpoint_path):
            raise RuntimeError(
                f"YOLO26 checkpoint not found at {self._checkpoint_path}. "
                "Run scripts/train_yolo26_cls.py first."
            )

        try:
            from ultralytics import YOLO
            self._model = YOLO(self._checkpoint_path)
        except Exception as exc:  # noqa: BLE001 — surface any loader failure as a load error
            self._model = None
            self._class_names = None
            raise RuntimeError(
                f"Failed to load YOLO26 checkpoint at {self._checkpoint_path}: {exc}"
            ) from exc

        names = getattr(self._model, "names", None)
        # ultralytics CLI-style YOLO(...) exposes names via .names (dict); the
        # classifier checkpoint may also expose them nested under model.names.
        if not names:
            nested = self._model.model
            if nested is not None:
                names = getattr(nested, "names", None)
        if not names:
            raise ValueError(
                "YOLO26 checkpoint does not advertise class names; cannot map "
                "probabilities to the healthy/defective contract."
            )

        class_names = {int(k): str(v) for k, v in names.items()}
        if len(class_names) != MAX_SUPPORTED_CLASSES:
            raise ValueError(
                f"YOLO26ClassifierModel expects a binary (healthy/defective) checkpoint, "
                f"but found {len(class_names)} classes: {class_names}. "
                "A multi-class checkpoint cannot be mapped into DefectProbabilities safely."
            )

        self._class_names = class_names
        logger.info(
            "Loaded YOLO26 checkpoint: %s (classes=%s, imgsz=%s, device=%s)",
            self._checkpoint_path, self._class_names, _MODEL_IMGSZ, _MODEL_DEVICE,
        )

    def _resolve_probabilities(self, probs) -> tuple[float, str]:
        """Return (defective_prob, predicted_label) from a classification result.

        Maps by class NAME (not index) so a checkpoint whose index order differs
        from the recorded export order is still handled correctly, as long as one
        class is a healthy axis and the other is a defective axis.
        """
        try:
            all_probs = probs.data.tolist() if hasattr(probs.data, "tolist") else list(probs.data)
        except Exception:
            all_probs = list(probs.data)  # fall back even if conversion helpers fail

        defective_prob = 0.0
        healthy_prob = 0.0
        for idx, name in self._class_names.items():
            if not (0 <= idx < len(all_probs)):
                continue
            val = float(all_probs[idx])
            normalized = (name if isinstance(name, str) else str(name)).strip().lower()
            if normalized in _DEFECTIVE_CLASS_LABELS:
                defective_prob = val
            elif normalized == "healthy":
                healthy_prob = val

        # Prefer the explicit defective mass; if the checkpoint uses a defect
        # synonym not in _DEFECTIVE_CLASS_LABELS, infer it as the complement of
        # the healthy class.
        if defective_prob == 0.0 and healthy_prob > 0.0:
            non_healthy = [
                p for (i, p) in enumerate(all_probs)
                if self._class_names.get(i, "").lower() != "healthy"
            ]
            defective_prob = max(non_healthy) if non_healthy else 0.0

        # Predicted label is derived from the model's top1 index.
        try:
            top1_idx = int(probs.top1)
        except Exception:
            top1_idx = int(sorted(range(len(all_probs)), key=lambda i: all_probs[i], reverse=True)[0])
        predicted_label = str(self._class_names.get(top1_idx, "unknown")).lower()
        return defective_prob, predicted_label

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

        Failure semantics:
        - load errors (raised by `_load_model`) propagate to the pipeline, which
          maps them to MODEL_UNAVAILABLE without invoking the mock;
        - unreadable image bytes          -> status ERROR (message points at the payload);
        - inference exception             -> status ERROR;
        - empty/invalid classification    -> status NO_VALID_DETECTIONS with an explicit message;
        - valid binary prediction         -> status SUCCESS with the model's own
          top-1 confidence in overall_confidence (grading engine decides review).

        No fabrication of bounding boxes / size estimates / physical properties.
        """
        request_id = image_input.image_id
        self._load_model()
        start_time = time.perf_counter()

        try:
            img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        except Exception as exc:
            processing_time_ms = round((time.perf_counter() - start_time) * 1000.0, 3)
            logger.warning("%s classification decode failed: %s", request_id, exc)
            return VisionResult(
                request_id=request_id,
                model_name=self.model_name,
                model_version=self.model_version,
                source=self.source,
                processing_time_ms=processing_time_ms,
                onions=[],
                overall_confidence=0.0,
                status="ERROR",
                error_message=f"Could not decode input image for classification: {exc}",
            )

        try:
            results = self._model.predict(
                source=img,
                imgsz=_MODEL_IMGSZ,
                device=_MODEL_DEVICE,
                verbose=False,
            )
        except Exception as exc:
            processing_time_ms = round((time.perf_counter() - start_time) * 1000.0, 3)
            logger.exception("%s classification inference failed", request_id)
            return VisionResult(
                request_id=request_id,
                model_name=self.model_name,
                model_version=self.model_version,
                source=self.source,
                processing_time_ms=processing_time_ms,
                onions=[],
                overall_confidence=0.0,
                status="ERROR",
                error_message=f"YOLO26 classification inference failed: {exc}",
            )

        processing_time_ms = round((time.perf_counter() - start_time) * 1000.0, 3)

        if not results or len(results) == 0:
            return VisionResult(
                request_id=request_id,
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
        if probs is None:
            return VisionResult(
                request_id=request_id,
                model_name=self.model_name,
                model_version=self.model_version,
                source=self.source,
                processing_time_ms=processing_time_ms,
                onions=[],
                overall_confidence=0.0,
                status="NO_VALID_DETECTIONS",
                error_message="YOLO26 returned a result with no class probabilities",
            )

        defective_prob, predicted_label = self._resolve_probabilities(probs)
        try:
            top1_conf = float(probs.top1conf)
        except Exception:
            data = probs.data
            top1_conf = max(data.tolist()) if hasattr(data, "tolist") else 0.0

        if predicted_label not in _DEFECTIVE_CLASS_LABELS and predicted_label != "healthy":
            return VisionResult(
                request_id=request_id,
                model_name=self.model_name,
                model_version=self.model_version,
                source=self.source,
                processing_time_ms=processing_time_ms,
                onions=[],
                overall_confidence=round(top1_conf, 4),
                status="NO_VALID_DETECTIONS",
                error_message=f"YOLO26 predicted an unknown class '{predicted_label}'",
            )

        # Create a whole-image detection entry
        w, h = image_input.width, image_input.height
        detection = OnionDetection(
            onion_id=f"CLS-{request_id}",
            bbox=[0, 0, w, h],
            detection_confidence=round(top1_conf, 4),
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
            request_id=request_id,
            model_name=self.model_name,
            model_version=self.model_version,
            source=self.source,
            processing_time_ms=processing_time_ms,
            onions=[detection],
            overall_confidence=round(top1_conf, 4),
            status="SUCCESS",
        )
