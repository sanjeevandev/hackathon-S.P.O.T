"""Unit tests for Model Registry, mock determinism, and production protection."""

import pytest
from backend.ai.mock_model import DevelopmentMockVisionModel
from backend.ai.schemas import ImageInput
from backend.ai.registry import get_vision_model, ProductionModelUnavailableError
from tests.fixtures import create_clean_image


def test_mock_model_is_deterministic():
    """Verify DevelopmentMockVisionModel produces identical outputs for identical inputs."""
    model = DevelopmentMockVisionModel()
    img_bytes = create_clean_image()
    image_input = ImageInput(image_id="REQ-DET-01", width=640, height=480)

    res1 = model.analyze(image_input, img_bytes)
    res2 = model.analyze(image_input, img_bytes)

    assert res1.source == "development_mock"
    assert res2.source == "development_mock"
    assert len(res1.onions) == len(res2.onions)
    assert res1.onions[0].bbox == res2.onions[0].bbox
    assert res1.onions[1].bbox == res2.onions[1].bbox
    assert res1.overall_confidence == res2.overall_confidence


def test_mock_model_explicit_source_identification():
    """Verify mock model result explicitly identifies source as development_mock."""
    model = DevelopmentMockVisionModel()
    assert model.source == "development_mock"

    img_bytes = create_clean_image()
    image_input = ImageInput(image_id="REQ-SRC-01", width=640, height=480)
    res = model.analyze(image_input, img_bytes)

    assert res.source == "development_mock"
    assert res.model_name == "DevelopmentMockVisionModel"


def test_production_mode_cannot_silently_use_mock():
    """Verify production mode returns a REAL model when one is available —
    and never silently falls back to DevelopmentMockVisionModel."""
    model = get_vision_model(environment="production")
    assert model.source == "real_model"
    assert model.source != "development_mock"


def test_production_mode_refuses_explicit_mock_request():
    """Verify that requesting DevelopmentMockVisionModel in production raises ProductionModelUnavailableError."""
    with pytest.raises(ProductionModelUnavailableError) as exc_info:
        get_vision_model(environment="production", model_name="DevelopmentMockVisionModel")

    assert "Forbidden" in str(exc_info.value)
