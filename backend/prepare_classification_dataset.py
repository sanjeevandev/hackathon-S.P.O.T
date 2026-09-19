"""
S.P.O.T. Agricultural Produce Optimization & Tracking
Preparation Script: Raw YOLO Object Detection BBoxes -> 4-Class Classification Dataset
SIH 2026 Procurement Quality Grading & Defect Detection Engine
"""

import os
import yaml
import logging
from typing import Dict, Optional, Tuple
import cv2

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DATASET_DIR = os.path.join(PROJECT_ROOT, "backend", "dataset_raw")
TARGET_DATASET_DIR = os.path.join(PROJECT_ROOT, "backend", "dataset_classification")
DATA_YAML_PATH = os.path.join(RAW_DATASET_DIR, "data.yaml")

# Exact target mapping specification
TARGET_NAME_MAP = {
    "RedOnion": "healthy",
    "WhiteOnion": "healthy",
    "BrownOnion": "healthy",
    "Mold": "disease",
    "Rot": "rotten",
    "Sprout": "sprouted",
}

# Classes to explicitly skip: DoubleSplit, FullPeeled Onion, HalfOnion, HalfPeeled Onion, Onionpeel, SpringOnion
MIN_CROP_DIM = 20
PADDING_RATIO = 0.10


def load_class_id_mapping(yaml_path: str) -> Dict[int, Optional[str]]:
    """Loads class definitions from data.yaml and resolves ID -> 4-class target category."""
    if not os.path.exists(yaml_path):
        raise FileNotFoundError(f"data.yaml not found at: {yaml_path}")

    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    raw_names = data.get("names", [])
    if isinstance(raw_names, dict):
        raw_names = [raw_names[k] for k in sorted(raw_names.keys())]

    logger.info("Found raw class names in data.yaml: %s", raw_names)

    id_to_target: Dict[int, Optional[str]] = {}
    for idx, name in enumerate(raw_names):
        target_cls = TARGET_NAME_MAP.get(name, None)
        id_to_target[idx] = target_cls
        logger.info("  Class ID %2d: '%s' -> %s", idx, name, f"'{target_cls}'" if target_cls else "SKIP")

    return id_to_target


def process_split(split_src_name: str, split_dst_name: str, id_to_target: Dict[int, Optional[str]]) -> Dict[str, int]:
    """Processes images and labels for a split (e.g. train -> train, valid -> val)."""
    src_images_dir = os.path.join(RAW_DATASET_DIR, split_src_name, "images")
    src_labels_dir = os.path.join(RAW_DATASET_DIR, split_src_name, "labels")

    if not os.path.exists(src_images_dir) or not os.path.exists(src_labels_dir):
        logger.warning("Split directories not found: %s or %s", src_images_dir, src_labels_dir)
        return {}

    # Target class subdirectories
    for target_cls in ["healthy", "disease", "rotten", "sprouted"]:
        os.makedirs(os.path.join(TARGET_DATASET_DIR, split_dst_name, target_cls), exist_ok=True)

    counters: Dict[str, int] = {"healthy": 0, "disease": 0, "rotten": 0, "sprouted": 0}
    skipped_count = 0
    small_crop_count = 0

    image_files = [f for f in sorted(os.listdir(src_images_dir)) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
    logger.info("Processing %d images in '%s' -> '%s'...", len(image_files), split_src_name, split_dst_name)

    for img_fname in image_files:
        base_name, _ = os.path.splitext(img_fname)
        label_fname = f"{base_name}.txt"
        img_path = os.path.join(src_images_dir, img_fname)
        label_path = os.path.join(src_labels_dir, label_fname)

        if not os.path.exists(label_path):
            continue

        img = cv2.imread(img_path)
        if img is None:
            logger.warning("Failed to read image: %s", img_path)
            continue

        img_h, img_w = img.shape[:2]

        with open(label_path, "r", encoding="utf-8") as lf:
            lines = [line.strip() for line in lf if line.strip()]

        for line_idx, line in enumerate(lines):
            parts = line.split()
            if len(parts) < 5:
                continue

            try:
                class_id = int(float(parts[0]))
                xc, yc, w_norm, h_norm = [float(p) for p in parts[1:5]]
            except Exception as parse_err:
                logger.warning("Malformed label line in %s: '%s' (%s)", label_fname, line, parse_err)
                continue

            target_cls = id_to_target.get(class_id)
            if not target_cls:
                skipped_count += 1
                continue

            # Convert normalized coordinates to absolute pixels
            box_w = w_norm * img_w
            box_h = h_norm * img_h
            cx = xc * img_w
            cy = yc * img_h

            x1 = cx - (box_w / 2.0)
            y1 = cy - (box_h / 2.0)
            x2 = cx + (box_w / 2.0)
            y2 = cy + (box_h / 2.0)

            # Apply ~10% padding
            pad_x = box_w * PADDING_RATIO
            pad_y = box_h * PADDING_RATIO

            px1 = max(0, int(round(x1 - pad_x)))
            py1 = max(0, int(round(y1 - pad_y)))
            px2 = min(img_w, int(round(x2 + pad_x)))
            py2 = min(img_h, int(round(y2 + pad_y)))

            crop_w = px2 - px1
            crop_h = py2 - py1

            if crop_w < MIN_CROP_DIM or crop_h < MIN_CROP_DIM:
                small_crop_count += 1
                logger.warning("Crop too small (%dx%d) in %s box %d. Skipping.", crop_w, crop_h, img_fname, line_idx)
                continue

            crop = img[py1:py2, px1:px2]
            if crop.size == 0:
                continue

            counters[target_cls] += 1
            out_filename = f"{target_cls}_{counters[target_cls]:05d}.jpg"
            out_path = os.path.join(TARGET_DATASET_DIR, split_dst_name, target_cls, out_filename)

            cv2.imwrite(out_path, crop)

    logger.info("Split '%s' -> '%s' complete:", split_src_name, split_dst_name)
    logger.info("  Crops generated: %s", counters)
    logger.info("  Skipped non-target boxes: %d", skipped_count)
    logger.info("  Skipped undersized crops (<%dpx): %d", MIN_CROP_DIM, small_crop_count)
    return counters


def main():
    print("=" * 70)
    print("🧅 S.P.O.T. Classification Dataset Preparation Engine")
    print("=" * 70)

    id_to_target = load_class_id_mapping(DATA_YAML_PATH)

    # Process train split
    train_counts = process_split("train", "train", id_to_target)

    # Process validation split (valid -> val)
    val_counts = process_split("valid", "val", id_to_target)

    print("\n" + "=" * 70)
    print("✅ DATASET EXTRACTION SUMMARY:")
    print("=" * 70)
    print("Train Split:")
    for cls_name, count in train_counts.items():
        print(f"  - backend/dataset_classification/train/{cls_name}: {count} images")
    print("\nValidation Split:")
    for cls_name, count in val_counts.items():
        print(f"  - backend/dataset_classification/val/{cls_name}: {count} images")
    print("=" * 70)


if __name__ == "__main__":
    main()
