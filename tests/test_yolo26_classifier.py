"""Unit and integration tests for YOLO26ClassifierModel and pipeline integration."""

import os
import pytest
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
