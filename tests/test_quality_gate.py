"""Unit tests for Image Quality Gate screening layer."""

import pytest
from backend.pipeline.quality_gate import ImageQualityGate
from backend.pipeline.config import QualityGateConfig
from tests.fixtures import (
    create_clean_image,
    create_blurry_image,
    create_dark_image,
    create_bright_image,
    create_low_res_image,
)


def test_clean_image_passes_quality_gate():
    """Verify clean, high-contrast image passes quality gate screening."""
    gate = ImageQualityGate()
    img_bytes = create_clean_image()
    res = gate.evaluate(img_bytes)

    assert res.status == "PASS"
    assert res.passed is True
    assert len(res.reasons) == 0


def test_blurry_image_fails_quality_gate():
    """Verify severely blurred image fails with IMAGE_TOO_BLURRY reason."""
    gate = ImageQualityGate()
    img_bytes = create_blurry_image()
    res = gate.evaluate(img_bytes)

    assert res.status == "RETAKE_REQUIRED"
    assert res.passed is False
    assert "IMAGE_TOO_BLURRY" in res.reasons


def test_dark_image_fails_quality_gate():
    """Verify underexposed dark image fails with IMAGE_TOO_DARK reason."""
    gate = ImageQualityGate()
    img_bytes = create_dark_image()
    res = gate.evaluate(img_bytes)

    assert res.status == "RETAKE_REQUIRED"
    assert res.passed is False
    assert "IMAGE_TOO_DARK" in res.reasons


def test_bright_image_fails_quality_gate():
    """Verify overexposed bright image fails with IMAGE_TOO_BRIGHT reason."""
    gate = ImageQualityGate()
    img_bytes = create_bright_image()
    res = gate.evaluate(img_bytes)

    assert res.status == "RETAKE_REQUIRED"
    assert res.passed is False
    assert "IMAGE_TOO_BRIGHT" in res.reasons


def test_low_res_image_fails_quality_gate():
    """Verify low resolution image fails with IMAGE_RESOLUTION_TOO_LOW reason."""
    gate = ImageQualityGate()
    img_bytes = create_low_res_image(100, 100)
    res = gate.evaluate(img_bytes)

    assert res.status == "RETAKE_REQUIRED"
    assert res.passed is False
    assert "IMAGE_RESOLUTION_TOO_LOW" in res.reasons
