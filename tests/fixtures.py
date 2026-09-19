"""Deterministic synthetic test image generator for S.P.O.T. unit tests.

Creates test images in memory without relying on external file dependencies:
- create_clean_image()
- create_blurry_image()
- create_dark_image()
- create_bright_image()
- create_low_res_image()
"""

import io
import numpy as np
from PIL import Image, ImageFilter


def create_clean_image(width: int = 640, height: int = 480) -> bytes:
    """Generates a high-contrast, well-illuminated synthetic image with sharp edge patterns."""
    arr = np.zeros((height, width, 3), dtype=np.uint8)
    # Fill neutral background
    arr[:, :] = [140, 120, 100]
    # Draw high-contrast shapes/grid for sharp edges
    for i in range(0, height, 40):
        arr[i:i+10, :, :] = [240, 240, 240]
    for j in range(0, width, 40):
        arr[:, j:j+10, :] = [30, 30, 30]

    img = Image.fromarray(arr)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    return buf.getvalue()


def create_blurry_image(width: int = 640, height: int = 480) -> bytes:
    """Generates a severely blurred synthetic image."""
    arr = np.zeros((height, width, 3), dtype=np.uint8)
    arr[:, :] = [140, 120, 100]
    # Smooth gradient without sharp edges
    for i in range(height):
        arr[i, :, 0] = int(100 + 50 * (i / height))
        arr[i, :, 1] = int(100 + 50 * (i / height))
        arr[i, :, 2] = int(100 + 50 * (i / height))

    img = Image.fromarray(arr).filter(ImageFilter.GaussianBlur(radius=25))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=50)
    return buf.getvalue()


def create_dark_image(width: int = 640, height: int = 480) -> bytes:
    """Generates an underexposed dark image (average pixel intensity < 20)."""
    arr = np.full((height, width, 3), 15, dtype=np.uint8)
    img = Image.fromarray(arr)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def create_bright_image(width: int = 640, height: int = 480) -> bytes:
    """Generates an overexposed bright image (average pixel intensity > 240)."""
    arr = np.full((height, width, 3), 250, dtype=np.uint8)
    img = Image.fromarray(arr)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def create_low_res_image(width: int = 100, height: int = 100) -> bytes:
    """Generates a low resolution image below minimum 320x240 threshold."""
    arr = np.full((height, width, 3), 128, dtype=np.uint8)
    img = Image.fromarray(arr)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()
