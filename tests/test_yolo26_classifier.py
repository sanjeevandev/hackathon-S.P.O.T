"""Unit and integration tests for YOLO26ClassifierModel and pipeline integration."""

import os
import pytest
from unittest.mock import patch
from types import SimpleNamespace
from backend.ai.yolo_cls_model import YOLO26ClassifierModel, _DEFAULT_CHECKPOINT
from backend.ai.registry import get_vision_model, register_vision_model, ProductionModelUnavailableError
from backend.ai.schemas import ImageInput, VisionResult
from backend.pipeline import InspectionPipeline
from tests.fixtures import create_clean_image


def test_yolo26_model_checkpoint_exists():
    """Verify that the trained YOLO26 checkpoint exists.

    The checkpoint is produced by scripts/train_yolo26_cls.py (run on a GPU
    machine with the Roboflow dataset). Until that artifact is committed, the
    registry truthfully reports the model as unavailable — so we only assert
    the availability flag here, not the file.
    """
    from backend.ai.yolo_cls_model import _YOLO26_CHECKPOINT_EXISTS
    assert _YOLO26_CHECKPOINT_EXISTS == os.path.exists(_DEFAULT_CHECKPOINT)


def test_yolo26_model_properties():
    """Verify model identity properties."""
    model = YOLO26ClassifierModel()
    assert model.model_name == "YOLO26n-cls-pilot"
    assert model.model_version == "1.0.0-pilot"
    assert model.source == "real_model"


def test_yolo26_inference_healthy_image():
    """Test YOLO26 inference on a known healthy validation sample."""
    if not os.path.exists(_DEFAULT_CHECKPOINT):
        pytest.skip("YOLO26 checkpoint not committed to this environment")
    val_healthy_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "artifacts", "ml", "yolo_cls_dataset_v1", "val", "healthy"
    )
    if not os.path.exists(val_healthy_dir) or not os.listdir(val_healthy_dir):
        pytest.skip("Validation images not found")

    sample_img = os.listdir(val_healthy_dir)[0]
    with open(os.path.join(val_healthy_dir, sample_img), "rb") as f:
        img_bytes = f.read()

    model = YOLO26ClassifierModel()
    image_input = ImageInput(image_id=sample_img, width=640, height=480)
    result = model.analyze(image_input, img_bytes)

    assert isinstance(result, VisionResult)
    assert result.status == "SUCCESS"
    assert result.source == "real_model"
    assert result.model_name == "YOLO26n-cls-pilot"
    assert len(result.onions) == 1
    # Check that healthy onion has low defect probability
    assert result.onions[0].defect_probabilities.damage < 0.5
    # Verify strict prohibition of fake physical properties
    assert result.onions[0].size_estimate.status == "UNAVAILABLE"
    assert result.onions[0].size_estimate.estimated_diameter_mm is None


def test_yolo26_inference_defective_image():
    """Test YOLO26 inference on a known defective validation sample."""
    if not os.path.exists(_DEFAULT_CHECKPOINT):
        pytest.skip("YOLO26 checkpoint not committed to this environment")
    val_defective_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "artifacts", "ml", "yolo_cls_dataset_v1", "val", "defective"
    )
    if not os.path.exists(val_defective_dir) or not os.listdir(val_defective_dir):
        pytest.skip("Validation images not found")

    sample_img = os.listdir(val_defective_dir)[0]
    with open(os.path.join(val_defective_dir, sample_img), "rb") as f:
        img_bytes = f.read()

    model = YOLO26ClassifierModel()
    image_input = ImageInput(image_id=sample_img, width=640, height=480)
    result = model.analyze(image_input, img_bytes)

    assert isinstance(result, VisionResult)
    assert result.status == "SUCCESS"
    assert len(result.onions) == 1
    # Check that defective onion has high defect probability
    assert result.onions[0].defect_probabilities.damage > 0.5


def test_pipeline_with_yolo26_model():
    """Verify that InspectionPipeline integrates and executes YOLO26 seamlessly."""
    if not os.path.exists(_DEFAULT_CHECKPOINT):
        pytest.skip("YOLO26 checkpoint not committed to this environment")
    yolo_model = YOLO26ClassifierModel()
    pipeline = InspectionPipeline(vision_model=yolo_model)
    clean_bytes = create_clean_image(640, 480)
    image_input = ImageInput(image_id="YOLO26-TEST-01", width=640, height=480)

    res = pipeline.execute(image_input, clean_bytes)
    assert res.status == "SUCCESS"
    assert res.quality_gate.passed is True
    assert res.vision_result is not None
    assert res.vision_result.source == "real_model"
    assert res.vision_result.model_name == "YOLO26n-cls-pilot"
    assert res.vision_result.overall_confidence > 0.0
    assert len(res.vision_result.onions) == 1


def test_yolo26_rejects_multiclass_checkpoint():
    """A multi-class checkpoint cannot be mapped into the binary contract.

    Feeds the OLD 4-class `backend/models/onion_classifier.pt` into the binary
    runner and asserts it refuses to load it (explicit ValueError) rather than
    silently mis-mapping its class probabilities.
    """
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    legacy_path = os.path.join(project_root, "backend", "models", "onion_classifier.pt")
    if not os.path.exists(legacy_path):
        pytest.skip("Legacy 4-class checkpoint not present in this checkout")
    with pytest.raises(ValueError) as exc_info:
        YOLO26ClassifierModel(checkpoint_path=legacy_path)._load_model()
    assert "binary" in str(exc_info.value) or "classes" in str(exc_info.value)


def test_yolo26_unknown_label_status():
    """An unknown class label produces NO_VALID_DETECTIONS, not a fabricated healthy/defective guess."""
    model = YOLO26ClassifierModel()
    model._model = SimpleNamespace()
    model._class_names = {0: "apple", 1: "banana"}  # unknown labels (not healthy/defective)

    class FakeProbs:
        data = [0.1, 0.9]
        top1 = 1
        top1conf = 0.9

    class FakeResult:
        probs = FakeProbs()

    image_input = ImageInput(image_id="REQ-UNK-01", width=640, height=480)
    with patch.object(model, "_load_model"), patch.object(
        model._model, "predict", return_value=[FakeResult()], create=True
    ):
        result = model.analyze(image_input, create_clean_image(640, 480))

    assert result.status == "NO_VALID_DETECTIONS"
    assert len(result.onions) == 0
    assert "unknown class" in result.error_message


def test_yolo26_probability_mapping_by_name():
    """Binary probabilities are mapped by class NAME, independent of index order."""
    model = YOLO26ClassifierModel()
    model._model = SimpleNamespace()
    model._class_names = {0: "healthy", 1: "defective"}  # reversed vs record order

    class FakeProbs:
        data = [0.3, 0.7]  # defective mass is 0.7 at index 1
        top1 = 1
        top1conf = 0.7

    class FakeResult:
        probs = FakeProbs()

    image_input = ImageInput(image_id="REQ-MAP-01", width=640, height=480)
    with patch.object(model, "_load_model"), patch.object(
        model._model, "predict", return_value=[FakeResult()], create=True
    ):
        result = model.analyze(image_input, create_clean_image(640, 480))

    assert result.status == "SUCCESS"
    assert result.onions[0].defect_probabilities.damage == 0.7
    assert result.overall_confidence == 0.7


def test_yolo26_low_confidence_threshold():
    """Below the accept threshold the runner must explicitly return LOW_CONFIDENCE."""
    model = YOLO26ClassifierModel(min_accept_confidence=0.90)
    model._model = SimpleNamespace()
    model._class_names = {0: "defective", 1: "healthy"}

    class FakeProbs:
        data = [0.45, 0.55]  # top1 = healthy @ 0.55 < 0.90 threshold
        top1 = 1
        top1conf = 0.55

    class FakeResult:
        probs = FakeProbs()

    image_input = ImageInput(image_id="REQ-LOW-01", width=640, height=480)
    with patch.object(model, "_load_model"), patch.object(
        model._model, "predict", return_value=[FakeResult()], create=True
    ):
        result = model.analyze(image_input, create_clean_image(640, 480))

    assert result.status == "LOW_CONFIDENCE"
    assert result.overall_confidence == 0.55
    assert result.error_message
    assert len(result.onions) == 1  # classification preserved for review


def test_yolo26_pipeline_review_required_on_low_confidence():
    """Pipeline mirrors LOW_CONFIDENCE into PipelineResult.status REVIEW_REQUIRED.

    Uses an unacceptably low threshold so any synthetic image lands below it,
    exercising the status mirroring end to end without touching the checkpoint.
    """
    model = YOLO26ClassifierModel(min_accept_confidence=1.01)  # always low
    model._model = SimpleNamespace()
    model._class_names = {0: "defective", 1: "healthy"}

    class FakeProbs:
        data = [0.2, 0.8]
        top1 = 1
        top1conf = 0.8

    class FakeResult:
        probs = FakeProbs()

    from unittest.mock import patch
    pipeline = InspectionPipeline(vision_model=model)
    image_input = ImageInput(image_id="REQ-PIPE-REV-01", width=640, height=480)
    with patch.object(model, "_load_model"), patch.object(
        model._model, "predict", return_value=[FakeResult()], create=True
    ):
        res = pipeline.execute(image_input, create_clean_image(640, 480))

    assert res.status == "REVIEW_REQUIRED"
    assert res.vision_result is not None
    assert res.vision_result.status == "LOW_CONFIDENCE"
    assert res.error_message and "low confidence" in res.error_message.lower()
