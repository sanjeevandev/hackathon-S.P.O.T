import io
import numpy as np
from PIL import Image
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.vision_service import validate_onion_image

client = TestClient(app)


def test_validate_onion_image_valid_onion():
    """Generates an image with onion-like brownish/reddish hues and verifies validation passes."""
    arr = np.zeros((300, 300, 3), dtype=np.uint8)
    # Neutral background
    arr[:, :] = [200, 200, 200]
    # Draw onion-colored bulb (RGB: [180, 70, 70] red onion / [190, 140, 60] brown onion)
    for y in range(80, 220):
        for x in range(80, 220):
            if (x - 150)**2 + (y - 150)**2 <= 60**2:
                arr[y, x] = [175, 75, 75]

    img = Image.fromarray(arr)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    img_bytes = buf.getvalue()

    is_valid, msg, metrics = validate_onion_image(img_bytes)
    assert is_valid is True
    assert "Valid" in msg
    assert metrics["onion_color_fraction"] > 0.04


def test_validate_onion_image_solid_color():
    """Solid color image lacks contrast / variance and should fail validation."""
    arr = np.full((200, 200, 3), 128, dtype=np.uint8)
    img = Image.fromarray(arr)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")

    is_valid, msg, metrics = validate_onion_image(buf.getvalue())
    assert is_valid is False
    assert "blank" in msg or "contrast" in msg


def test_validate_onion_image_non_onion_blue():
    """Pure blue screen has zero onion hues and should fail validation."""
    arr = np.zeros((200, 200, 3), dtype=np.uint8)
    arr[:, :] = [20, 50, 230] # Vibrant blue
    # Add contrast lines so contrast std is high
    arr[0:50, :, :] = [0, 0, 180]
    img = Image.fromarray(arr)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")

    is_valid, msg, metrics = validate_onion_image(buf.getvalue())
    assert is_valid is False
    assert "look like onions" in msg


def test_validate_onion_image_too_small():
    """Image below 100x100 resolution fails validation."""
    arr = np.full((50, 50, 3), 150, dtype=np.uint8)
    img = Image.fromarray(arr)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")

    is_valid, msg, metrics = validate_onion_image(buf.getvalue())
    assert is_valid is False
    assert "too low" in msg


def test_api_analyze_onion_validation_422():
    """POST /api/v1/analyze-onion with a solid image returns 422 with actionable detail."""
    arr = np.full((200, 200, 3), 128, dtype=np.uint8)
    img = Image.fromarray(arr)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")

    response = client.post(
        "/api/v1/analyze-onion",
        files={"file": ("test_blank.jpg", buf.getvalue(), "image/jpeg")}
    )
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
