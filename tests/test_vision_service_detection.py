import os
import cv2
import numpy as np
import pytest
from backend.services.vision_service import (
    detect_onions_opencv,
    run_yolov8_opencv_inference,
    AIVisionService,
    MIN_CONTOUR_AREA_PX,
    MAX_CONTOUR_AREA_RATIO,
    calibrate_pixel_to_mm_ratio
)
from backend.schemas import OnionAnalysisResponse, BoundingBoxItem

def test_detect_onions_empty_bytes():
    assert detect_onions_opencv(b"") == []

def test_detect_onions_corrupted_bytes():
    assert detect_onions_opencv(b"corrupted_byte_data_not_an_image") == []

def test_detect_onions_synthetic_image():
    # Create a synthetic image with 3 distinct circular blobs on a bright background
    img = np.full((500, 500, 3), 220, dtype=np.uint8)
    
    # Draw 3 dark circles (onion blobs) with areas > 400px
    cv2.circle(img, (120, 120), 40, (30, 40, 100), -1)  # radius 40 -> area ~ 5026 px
    cv2.circle(img, (350, 150), 30, (40, 50, 110), -1)  # radius 30 -> area ~ 2827 px
    cv2.circle(img, (250, 350), 35, (35, 45, 105), -1)  # radius 35 -> area ~ 3848 px
    
    success, encoded = cv2.imencode(".jpg", img)
    assert success
    img_bytes = encoded.tobytes()
    
    detections = detect_onions_opencv(img_bytes)
    assert len(detections) == 3
    for d in detections:
        assert "bbox" in d
        assert len(d["bbox"]) == 4
        assert d["area_px"] >= MIN_CONTOUR_AREA_PX
        assert d["diameter_px"] > 0
        x1, y1, x2, y2 = d["bbox"]
        assert x1 < x2 and y1 < y2

def test_detect_onions_real_photo():
    sample_path = "public/onions/onion_sample_1.jpg"
    if os.path.exists(sample_path):
        with open(sample_path, "rb") as f:
            img_bytes = f.read()
        detections = detect_onions_opencv(img_bytes)
        assert len(detections) > 0
        for d in detections:
            assert "bbox" in d
            assert "area_px" in d
            assert "diameter_px" in d
            assert d["area_px"] >= MIN_CONTOUR_AREA_PX

def test_ai_vision_service_process_onion_image():
    sample_path = "public/onions/onion_sample_1.jpg"
    if os.path.exists(sample_path):
        with open(sample_path, "rb") as f:
            img_bytes = f.read()
        resp = AIVisionService.process_onion_image(img_bytes, "test_onion.jpg")
        assert isinstance(resp, OnionAnalysisResponse)
        assert resp.filename == "test_onion.jpg"
        assert resp.bounding_boxes is not None
        assert len(resp.bounding_boxes) > 0
        for item in resp.bounding_boxes:
            assert isinstance(item, BoundingBoxItem)
            assert item.class_label in ("grade_a", "grade_urs", "undersized", "damaged", "rotten", "sprouted")
            assert item.confidence > 0.0
            assert len(item.bbox) == 4
            assert item.diameter_mm > 0
