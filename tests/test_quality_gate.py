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


def test_non_onion_image_fails_quality_gate():
    """Verify non-onion input (e.g. artificial blue screen) is rejected before quality classification."""
    import io
    import numpy as np
    from PIL import Image

    # Create artificial vivid blue test image
    arr = np.zeros((480, 640, 3), dtype=np.uint8)
    arr[:, :] = [20, 80, 240]  # Vivid blue non-onion
    # Add some high contrast stripes to pass blur and contrast checks
    for i in range(0, 480, 50):
        arr[i:i+10, :, :] = [10, 50, 200]

    img = Image.fromarray(arr)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    non_onion_bytes = buf.getvalue()

    gate = ImageQualityGate()
    res = gate.evaluate(non_onion_bytes)

    assert res.status == "REJECTED_NOT_ONION"
    assert res.passed is False
    assert "NOT_AN_ONION" in res.reasons
    assert any("Scan onion only" in r for r in res.recommendations)

