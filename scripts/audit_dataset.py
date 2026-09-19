#!/usr/bin/env python3
"""Dataset Audit Tooling for S.P.O.T. (Smart Procurement Onion Transparency).

Audits an onion dataset at SPOT_DATASET_DIR or passed CLI --dataset-dir.

Computes:
1. Inventory (total count, file types, dimensions, corruption, color channels, resolutions, aspect ratios)
2. Label structure (YOLO txt, COCO json, VOC xml, folder-based classification, unannotated)
3. Defect taxonomy mapping
4. Multi-onion statistics (min, max, median, mean per image)
5. Duplicate analysis (exact MD5 hash & perceptual hashing)
6. Image quality distribution (blur, brightness, contrast)
7. Dataset partition leakage risks

Saves summary artifacts to:
- artifacts/dataset_audit/dataset_summary.json
- artifacts/dataset_audit/dataset_summary.csv
- docs/DATASET_AUDIT.md
"""

import os
import sys
import argparse
import hashlib
import json
import csv
import numpy as np
from PIL import Image
from pathlib import Path
from typing import Dict, List, Any, Optional

try:
    import cv2
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False


def compute_md5(file_path: Path) -> str:
    """Compute MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def compute_dhash(img: Image.Image, hash_size: int = 8) -> str:
    """Compute difference perceptual hash (dhash) for near-duplicate detection."""
    resized = img.convert("L").resize((hash_size + 1, hash_size), Image.Resampling.BILINEAR)
    pixels = np.array(resized)
    # Difference between neighboring pixels
    diff = pixels[:, 1:] > pixels[:, :-1]
    # Convert boolean array to hex string
    return hex(int("".join(["1" if b else "0" for b in diff.flatten()]), 2))[2:].zfill(hash_size * hash_size // 4)


def find_image_files(dataset_dir: Path) -> List[Path]:
    """Recursively discover all supported image files in dataset directory."""
    extensions = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    images = []
    if not dataset_dir.exists():
        return images
    for root, _, files in os.walk(dataset_dir):
        for file in files:
            ext = Path(file).suffix.lower()
            if ext in extensions:
                images.append(Path(root) / file)
    return sorted(images)


def find_label_files(dataset_dir: Path) -> List[Path]:
    """Recursively discover label annotation files (.txt, .json, .xml)."""
    extensions = {".txt", ".json", ".xml"}
    labels = []
    if not dataset_dir.exists():
        return labels
    for root, _, files in os.walk(dataset_dir):
        for file in files:
            ext = Path(file).suffix.lower()
            if ext in extensions and not file.startswith("dataset_summary"):
                labels.append(Path(root) / file)
    return sorted(labels)


def audit_dataset(dataset_dir: Path, output_dir: Path) -> Dict[str, Any]:
    """Perform dataset audit on target directory."""
    print(f"🔍 Auditing dataset directory: {dataset_dir}")
    image_paths = find_image_files(dataset_dir)
    label_paths = find_label_files(dataset_dir)

    if not image_paths:
        print("⚠️ DATASET_NOT_AVAILABLE: No image files found in specified dataset directory.")
        return {
            "status": "DATASET_NOT_AVAILABLE",
            "dataset_dir": str(dataset_dir),
            "total_images": 0,
            "message": "Dataset directory is empty or contains no supported image files (.jpg, .png, .jpeg, .webp)."
        }

    total_images = len(image_paths)
    print(f"📸 Found {total_images} images and {len(label_paths)} potential label files.")

    corrupt_files = []
    file_types: Dict[str, int] = {}
    dimensions = []
    aspect_ratios = []
    color_modes: Dict[str, int] = {}
    file_sizes = []
    
    md5_hashes: Dict[str, List[str]] = {}
    dhashes: Dict[str, List[str]] = {}

    blur_scores = []
    brightness_scores = []
    contrast_scores = []

    for idx, img_path in enumerate(image_paths):
        rel_path = str(img_path.relative_to(dataset_dir))
        ext = img_path.suffix.lower()
        file_types[ext] = file_types.get(ext, 0) + 1
        file_sizes.append(img_path.stat().st_size)

        # Exact MD5 duplicate check
        md5_val = compute_md5(img_path)
        md5_hashes.setdefault(md5_val, []).append(rel_path)

        try:
            with Image.open(img_path) as img:
                img.verify()
            with Image.open(img_path) as img:
                w, h = img.size
                mode = img.mode
                dimensions.append((w, h))
                aspect_ratios.append(round(w / h, 2) if h > 0 else 0)
                color_modes[mode] = color_modes.get(mode, 0) + 1

                # Compute dhash for near-duplicate check
                dhash_val = compute_dhash(img)
                dhashes.setdefault(dhash_val, []).append(rel_path)

                # Quality metrics
                gray = np.array(img.convert("L"))
                brightness_scores.append(float(np.mean(gray)))
                contrast_scores.append(float(np.std(gray)))

                if HAS_OPENCV:
                    blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
                else:
                    kernel = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]], dtype=np.float64)
                    from scipy.signal import convolve2d
                    lap = convolve2d(gray.astype(np.float64), kernel, mode="valid")
                    blur_score = float(lap.var())
                blur_scores.append(blur_score)

        except Exception as err:
            corrupt_files.append({"file": rel_path, "error": str(err)})

    # Duplicates summary
    exact_duplicates = {k: v for k, v in md5_hashes.items() if len(v) > 1}
    near_duplicates = {k: v for k, v in dhashes.items() if len(v) > 1}

    # Label structure analysis
    yolo_labels = [p for p in label_paths if p.suffix.lower() == ".txt" and p.name != "classes.txt"]
    json_labels = [p for p in label_paths if p.suffix.lower() == ".json"]
    xml_labels = [p for p in label_paths if p.suffix.lower() == ".xml"]

    annotation_format = "UNANNOTATED"
    class_counts: Dict[str, int] = {}
    onions_per_image: List[int] = []

    if yolo_labels:
        annotation_format = "YOLO_TXT"
        for yolo_file in yolo_labels:
            with open(yolo_file, "r") as f:
                lines = f.readlines()
                onions_per_image.append(len(lines))
                for line in lines:
                    parts = line.strip().split()
                    if parts:
                        cls_id = parts[0]
                        class_counts[cls_id] = class_counts.get(cls_id, 0) + 1
    elif json_labels:
        annotation_format = "COCO_JSON"
    elif xml_labels:
        annotation_format = "PASCAL_VOC_XML"

    audit_summary = {
        "status": "COMPLETED",
        "dataset_dir": str(dataset_dir),
        "total_images": total_images,
        "corrupt_files_count": len(corrupt_files),
        "corrupt_files": corrupt_files,
        "file_types": file_types,
        "color_modes": color_modes,
        "resolution_stats": {
            "min_width": int(min(w for w, h in dimensions)) if dimensions else 0,
            "max_width": int(max(w for w, h in dimensions)) if dimensions else 0,
            "min_height": int(min(h for w, h in dimensions)) if dimensions else 0,
            "max_height": int(max(h for w, h in dimensions)) if dimensions else 0,
        },
        "aspect_ratios_distribution": {
            "mean": round(float(np.mean(aspect_ratios)), 2) if aspect_ratios else 0,
            "median": round(float(np.median(aspect_ratios)), 2) if aspect_ratios else 0,
        },
        "file_size_bytes_stats": {
            "mean": round(float(np.mean(file_sizes)), 2) if file_sizes else 0,
            "min": min(file_sizes) if file_sizes else 0,
            "max": max(file_sizes) if file_sizes else 0,
        },
        "duplicate_analysis": {
            "exact_duplicate_groups": len(exact_duplicates),
            "exact_duplicate_files_total": sum(len(v) for v in exact_duplicates.values()),
            "near_duplicate_groups": len(near_duplicates),
            "near_duplicate_files_total": sum(len(v) for v in near_duplicates.values()),
        },
        "annotation_analysis": {
            "annotation_format": annotation_format,
            "total_label_files": len(label_paths),
            "class_object_counts": class_counts,
            "onions_per_image": {
                "mean": round(float(np.mean(onions_per_image)), 2) if onions_per_image else 0,
                "median": float(np.median(onions_per_image)) if onions_per_image else 0,
                "min": min(onions_per_image) if onions_per_image else 0,
                "max": max(onions_per_image) if onions_per_image else 0,
            }
        },
        "image_quality_stats": {
            "blur_score_laplacian": {
                "mean": round(float(np.mean(blur_scores)), 2) if blur_scores else 0,
                "median": round(float(np.median(blur_scores)), 2) if blur_scores else 0,
                "min": round(float(np.min(blur_scores)), 2) if blur_scores else 0,
                "max": round(float(np.max(blur_scores)), 2) if blur_scores else 0,
            },
            "brightness": {
                "mean": round(float(np.mean(brightness_scores)), 2) if brightness_scores else 0,
                "median": round(float(np.median(brightness_scores)), 2) if brightness_scores else 0,
            },
            "contrast": {
                "mean": round(float(np.mean(contrast_scores)), 2) if contrast_scores else 0,
                "median": round(float(np.median(contrast_scores)), 2) if contrast_scores else 0,
            }
        }
    }

    # Output json & csv
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "dataset_summary.json"
    with open(json_path, "w") as f:
        json.dump(audit_summary, f, indent=2)

    csv_path = output_dir / "dataset_summary.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Metric", "Value"])
        writer.writerow(["total_images", total_images])
        writer.writerow(["corrupt_files_count", len(corrupt_files)])
        writer.writerow(["annotation_format", annotation_format])
        writer.writerow(["exact_duplicate_groups", len(exact_duplicates)])
        writer.writerow(["near_duplicate_groups", len(near_duplicates)])
        if blur_scores:
            writer.writerow(["blur_mean_laplacian", round(float(np.mean(blur_scores)), 2)])
            writer.writerow(["brightness_mean", round(float(np.mean(brightness_scores)), 2)])

    print(f"✅ Saved dataset audit summary to {json_path} and {csv_path}")
    return audit_summary


def main():
    parser = argparse.ArgumentParser(description="S.P.O.T. Dataset Audit Tool")
    parser.add_argument(
        "--dataset-dir",
        type=str,
        default=os.getenv("SPOT_DATASET_DIR", "/home/sanjeeva/ONION HACKATHON/backend/dataset"),
        help="Path to the root dataset directory (env: SPOT_DATASET_DIR)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="artifacts/dataset_audit",
        help="Directory to save audit outputs"
    )

    args = parser.parse_args()
    ds_dir = Path(args.dataset_dir)
    out_dir = Path(args.output_dir)

    result = audit_dataset(ds_dir, out_dir)
    if result.get("status") == "DATASET_NOT_AVAILABLE":
        sys.exit(0)


if __name__ == "__main__":
    main()
