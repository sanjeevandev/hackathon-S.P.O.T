import os
import sys
import json
import csv
import hashlib
import time
import math
import zipfile
import datetime
from collections import defaultdict
import numpy as np
import cv2
from concurrent.futures import ThreadPoolExecutor

SOURCE_PATH = "/run/media/sanjeeva/New Volume1/ONION IQ/Image Dataset of Red and White Onion Bulbs and Lea"
ZIP_NAME = "Onion Leaves and Bulb Dataset.zip"
ZIP_PATH = os.path.join(SOURCE_PATH, ZIP_NAME)

OUTPUT_DIR = "artifacts/dataset_audit"
DOCS_DIR = "docs"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(DOCS_DIR, exist_ok=True)

start_time = time.time()
audit_timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Step 1: Verifying Dataset Path & Archive...")
path_exists = os.path.exists(SOURCE_PATH)
zip_exists = os.path.exists(ZIP_PATH)

if not zip_exists:
    print(f"Error: Archive not found at {ZIP_PATH}")
    sys.exit(1)

zip_file_size = os.path.getsize(ZIP_PATH)
print(f"Source Directory Exists: {path_exists}")
print(f"Zip Archive Exists: {zip_exists} ({zip_file_size} bytes / {zip_file_size/(1024*1024):.2f} MB)")

print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Step 2: Streaming ZIP Entries sequentially into RAM...")

items_to_process = []
with zipfile.ZipFile(ZIP_PATH, 'r') as z:
    infolist = z.infolist()
    total_files = len(infolist)
    print(f"Total entries in archive: {total_files}")
    for idx, info in enumerate(infolist):
        if info.is_dir():
            continue
        data = z.read(info.filename)
        items_to_process.append((info.filename, data))

print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Read {len(items_to_process)} files into RAM in {time.time()-start_time:.2f}s")

def process_item(item):
    filename, data = item
    file_size = len(data)
    sha256_hash = hashlib.sha256(data).hexdigest()
    parts = filename.split('/')
    file_ext = parts[-1].split('.')[-1].lower() if '.' in parts[-1] else 'no_ext'
    class_folder = '/'.join(parts[:-1])
    basename = parts[-1]

    is_image_ext = file_ext in ['jpg', 'jpeg', 'png', 'webp', 'bmp', 'tiff']

    if not is_image_ext:
        return {
            'filename': filename,
            'basename': basename,
            'file_ext': file_ext,
            'class_folder': class_folder,
            'is_image': False,
            'valid': False,
            'corrupt': False,
            'file_size': file_size,
            'sha256': sha256_hash,
            'error': 'Non-image extension'
        }

    img_arr = np.frombuffer(data, np.uint8)
    img = cv2.imdecode(img_arr, cv2.IMREAD_COLOR)

    if img is None:
        return {
            'filename': filename,
            'basename': basename,
            'file_ext': file_ext,
            'class_folder': class_folder,
            'is_image': True,
            'valid': False,
            'corrupt': True,
            'file_size': file_size,
            'sha256': sha256_hash,
            'error': 'OpenCV decoding failed'
        }

    h, w, c = img.shape
    aspect_ratio = round(w / h, 4) if h > 0 else 0

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    brightness = float(np.mean(gray))
    contrast = float(np.std(gray))
    
    underexposed_ratio = float(np.sum(gray < 10) / gray.size)
    overexposed_ratio = float(np.sum(gray > 245) / gray.size)

    resized_gray = cv2.resize(gray, (9, 8), interpolation=cv2.INTER_AREA)
    diff = resized_gray[:, 1:] > resized_gray[:, :-1]
    dhash = 0
    for bit in diff.flatten():
        dhash = (dhash << 1) | int(bit)

    is_leaf = "1. Leaves" in class_folder
    is_bulb = "2. Bulb" in class_folder
    is_healthy = "1. Healthy" in class_folder
    is_unhealthy = "2. Unhealthy" in class_folder
    is_red = "1. Red Onion" in class_folder
    is_white = "2. White Onion" in class_folder
    is_single = "1. Single" in class_folder
    is_multiple = "2. Multiple" in class_folder

    scope = "OUT_OF_SCOPE_FOR_BULB_GRADING" if is_leaf else "BULB_GRADING"

    return {
        'filename': filename,
        'basename': basename,
        'file_ext': file_ext,
        'class_folder': class_folder,
        'is_image': True,
        'valid': True,
        'corrupt': False,
        'file_size': file_size,
        'sha256': sha256_hash,
        'dhash': f"{dhash:016x}",
        'width': w,
        'height': h,
        'channels': c,
        'aspect_ratio': aspect_ratio,
        'blur_score': round(blur_score, 2),
        'brightness': round(brightness, 2),
        'contrast': round(contrast, 2),
        'underexposed_ratio': round(underexposed_ratio, 4),
        'overexposed_ratio': round(overexposed_ratio, 4),
        'is_leaf': is_leaf,
        'is_bulb': is_bulb,
        'is_healthy': is_healthy,
        'is_unhealthy': is_unhealthy,
        'is_red': is_red,
        'is_white': is_white,
        'is_single': is_single,
        'is_multiple': is_multiple,
        'scope': scope
    }

print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Step 3: Decoding & Extracting Quality Metrics in Parallel...")
t_cpu = time.time()
with ThreadPoolExecutor(max_workers=12) as executor:
    results = list(executor.map(process_item, items_to_process))

print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Processed {len(results)} images in {time.time()-t_cpu:.2f}s")

print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Step 4: Deduplication Analysis...")

sha_groups = defaultdict(list)
dhash_map = {}
valid_images = []
corrupt_images = []
unsupported_files = []

for r in results:
    if not r['is_image']:
        unsupported_files.append(r)
        continue
    if r['corrupt']:
        corrupt_images.append(r)
        continue

    valid_images.append(r)
    sha_groups[r['sha256']].append(r['filename'])
    dhash_map[r['filename']] = int(r['dhash'], 16)

exact_duplicate_groups = {k: v for k, v in sha_groups.items() if len(v) > 1}
exact_duplicate_file_count = sum(len(v) for v in exact_duplicate_groups.values())
exact_duplicate_redundant_count = sum(len(v)-1 for v in exact_duplicate_groups.values())

print(f"Exact Duplicate SHA-256 Groups: {len(exact_duplicate_groups)}")
print(f"Total files in exact duplicate groups: {exact_duplicate_file_count} (Redundant: {exact_duplicate_redundant_count})")

# Perceptual hash near-duplicate analysis
prefix_buckets = defaultdict(list)
for fn, val in dhash_map.items():
    prefix = val >> 48
    prefix_buckets[prefix].append((fn, val))

def popcount64(x):
    return bin(x).count('1')

near_duplicate_pairs = []
seen_pairs = set()

for p, items in prefix_buckets.items():
    n = len(items)
    for i in range(n):
        fn1, h1 = items[i]
        for j in range(i+1, n):
            fn2, h2 = items[j]
            dist = popcount64(h1 ^ h2)
            if dist <= 3:
                pair_key = tuple(sorted([fn1, fn2]))
                if pair_key not in seen_pairs:
                    seen_pairs.add(pair_key)
                    near_duplicate_pairs.append({
                        'file1': fn1,
                        'file2': fn2,
                        'hamming_distance': dist
                    })

print(f"Discovered near-duplicate pairs (dhash distance <= 3): {len(near_duplicate_pairs)}")

print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Step 5: Writing JSON/CSV Artifacts...")

inventory_summary = {
    'audit_timestamp': audit_timestamp,
    'source_path': SOURCE_PATH,
    'archive_path': ZIP_PATH,
    'total_files_in_archive': len(results),
    'image_files_count': len(valid_images) + len(corrupt_images),
    'valid_image_count': len(valid_images),
    'corrupt_image_count': len(corrupt_images),
    'non_image_files_count': len(unsupported_files),
    'format_breakdown': {'jpg': len(results)},
    'total_archive_size_bytes': zip_file_size
}

with open(os.path.join(OUTPUT_DIR, 'file_inventory.json'), 'w') as f:
    json.dump({
        'summary': inventory_summary,
        'files': results
    }, f, indent=2)

with open(os.path.join(OUTPUT_DIR, 'file_inventory.csv'), 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['file_path', 'filename', 'file_extension', 'file_size_bytes', 'is_image', 'valid', 'class_folder', 'sha256'])
    for r in results:
        writer.writerow([r['filename'], r['basename'], r['file_ext'], r['file_size'], r['is_image'], r.get('valid', False), r['class_folder'], r['sha256']])

# class_distribution.csv
class_counts = defaultdict(int)
class_samples = {}
class_scope = {}

for r in valid_images:
    cf = r['class_folder']
    class_counts[cf] += 1
    if cf not in class_samples:
        class_samples[cf] = r['filename']
        class_scope[cf] = r['scope']

total_valid = len(valid_images)

with open(os.path.join(OUTPUT_DIR, 'class_distribution.csv'), 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['class_name', 'source_directory', 'image_count', 'percentage_of_total', 'scope_category', 'sample_filename'])
    for cf, count in sorted(class_counts.items()):
        percentage = round((count / total_valid) * 100, 4)
        clean_name = cf.replace("New Onion - Copy/", "")
        writer.writerow([clean_name, cf, count, percentage, class_scope[cf], class_samples[cf]])

# duplicate_report.json
with open(os.path.join(OUTPUT_DIR, 'duplicate_report.json'), 'w') as f:
    json.dump({
        'audit_timestamp': audit_timestamp,
        'exact_duplicate_group_count': len(exact_duplicate_groups),
        'exact_duplicate_total_files': exact_duplicate_file_count,
        'exact_duplicate_redundant_files': exact_duplicate_redundant_count,
        'exact_duplicate_groups': exact_duplicate_groups,
        'near_duplicate_pair_count': len(near_duplicate_pairs),
        'near_duplicate_pairs': near_duplicate_pairs[:500]
    }, f, indent=2)

# image_quality_report.json
blurs = [r['blur_score'] for r in valid_images]
brights = [r['brightness'] for r in valid_images]
contrasts = [r['contrast'] for r in valid_images]
widths = [r['width'] for r in valid_images]
heights = [r['height'] for r in valid_images]
aspect_ratios = [r['aspect_ratio'] for r in valid_images]

resolutions_count = defaultdict(int)
for r in valid_images:
    resolutions_count[f"{r['width']}x{r['height']}"] += 1

image_quality_data = {
    'audit_timestamp': audit_timestamp,
    'total_evaluated_images': len(valid_images),
    'resolution_distribution': dict(resolutions_count),
    'blur_statistics': {
        'mean': round(float(np.mean(blurs)), 2),
        'min': round(float(np.min(blurs)), 2),
        'max': round(float(np.max(blurs)), 2),
        'std': round(float(np.std(blurs)), 2),
        'blurry_images_count_threshold_100': sum(1 for b in blurs if b < 100)
    },
    'brightness_statistics': {
        'mean': round(float(np.mean(brights)), 2),
        'min': round(float(np.min(brights)), 2),
        'max': round(float(np.max(brights)), 2),
        'std': round(float(np.std(brights)), 2),
        'underexposed_count': sum(1 for r in valid_images if r['underexposed_ratio'] > 0.3),
        'overexposed_count': sum(1 for r in valid_images if r['overexposed_ratio'] > 0.3)
    },
    'contrast_statistics': {
        'mean': round(float(np.mean(contrasts)), 2),
        'min': round(float(np.min(contrasts)), 2),
        'max': round(float(np.max(contrasts)), 2),
        'std': round(float(np.std(contrasts)), 2)
    },
    'aspect_ratio_statistics': {
        'min': round(float(np.min(aspect_ratios)), 4),
        'max': round(float(np.max(aspect_ratios)), 4),
        'mean': round(float(np.mean(aspect_ratios)), 4)
    }
}

with open(os.path.join(OUTPUT_DIR, 'image_quality_report.json'), 'w') as f:
    json.dump(image_quality_data, f, indent=2)

# DATASET_MANIFEST.json
manifest_sha256 = hashlib.sha256()
for r in sorted(valid_images, key=lambda x: x['filename']):
    manifest_sha256.update(f"{r['filename']}:{r['sha256']}\n".encode('utf-8'))

dataset_manifest = {
    'dataset_name': "Image Dataset of Red and White Onion Bulbs and Leaves",
    'source_path': SOURCE_PATH,
    'archive_name': ZIP_NAME,
    'archive_size_bytes': zip_file_size,
    'audit_timestamp': audit_timestamp,
    'dataset_manifest_checksum_sha256': manifest_sha256.hexdigest(),
    'total_files': len(results),
    'valid_images': len(valid_images),
    'corrupt_images': len(corrupt_images),
    'non_image_files': len(unsupported_files)
}

with open(os.path.join(OUTPUT_DIR, 'DATASET_MANIFEST.json'), 'w') as f:
    json.dump(dataset_manifest, f, indent=2)

print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Step 6: Complete Forensic Audit finished in {time.time()-start_time:.2f}s!")
