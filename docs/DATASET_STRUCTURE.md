# S.P.O.T. Dataset Forensic Audit: Directory & Label Structure

## 1. Overview & Storage Topology

The S.P.O.T. Phase 9 Forensic Audit inspected the real onion dataset located on physical partition `/dev/sdd5` mounted at `/run/media/sanjeeva/New Volume1/ONION IQ/Image Dataset of Red and White Onion Bulbs and Lea/Onion Leaves and Bulb Dataset.zip`.

- **Source Dataset Path**: `/run/media/sanjeeva/New Volume1/ONION IQ/Image Dataset of Red and White Onion Bulbs and Lea`
- **Archive Name**: `Onion Leaves and Bulb Dataset.zip`
- **Archive Size**: 1,608,618,402 bytes (~1.53 GB)
- **Total Files**: 16,300 (100% JPEG images)
- **Read-Only Compliance**: Source archive remained completely untouched and unmodified.

---

## 2. Directory Hierarchy & Label Encoding

Ground-truth annotations in this dataset are encoded **exclusively through directory path hierarchy**. There are no external metadata files, bounding box files, COCO JSON files, XML files, or segmentation masks.

```
Onion Leaves and Bulb Dataset.zip
└── New Onion - Copy/
    ├── 1. Leaves/                       [OUT_OF_SCOPE_FOR_BULB_GRADING]
    │   ├── 1. Healthy/
    │   │   ├── 1. Single                (1,010 images)
    │   │   └── 2. Multiple              (1,010 images)
    │   └── 2. Unhealthy/
    │       ├── 1. Single                (1,010 images)
    │       └── 2. Multiple              (1,010 images)
    └── 2. Bulb/                         [BULB_GRADING]
        ├── 1. Healthy/
        │   ├── 1. Red Onion/
        │   │   ├── 1. Single            (3,000 images)
        │   │   └── 2. Multiple          (1,110 images)
        │   └── 2. White Onion/
        │       ├── 1. Single            (3,000 images)
        │       └── 2. Multiple          (1,110 images)
        └── 2. Unhealthy/
            ├── 1. Red Onion/
            │   ├── 1. Single            (1,010 images)
            │   └── 2. Multiple          (1,010 images)
            └── 2. White Onion/
                ├── 1. Single            (1,010 images)
                └── 2. Multiple          (1,010 images)
```

---

## 3. Class Directory Inventory

| Directory Path | Image Count | % of Dataset | Organ | Health | Color | Arrangement | Scope |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `1. Leaves/1. Healthy/1. Single` | 1,010 | 6.20% | Leaf | Healthy | N/A | Single | OUT_OF_SCOPE |
| `1. Leaves/1. Healthy/2. Multiple` | 1,010 | 6.20% | Leaf | Healthy | N/A | Multiple | OUT_OF_SCOPE |
| `1. Leaves/2. Unhealthy/1. Single` | 1,010 | 6.20% | Leaf | Unhealthy | N/A | Single | OUT_OF_SCOPE |
| `1. Leaves/2. Unhealthy/2. Multiple` | 1,010 | 6.20% | Leaf | Unhealthy | N/A | Multiple | OUT_OF_SCOPE |
| `2. Bulb/1. Healthy/1. Red Onion/1. Single` | 3,000 | 18.40% | Bulb | Healthy | Red | Single | BULB_GRADING |
| `2. Bulb/1. Healthy/1. Red Onion/2. Multiple` | 1,110 | 6.81% | Bulb | Healthy | Red | Multiple | BULB_GRADING |
| `2. Bulb/1. Healthy/2. White Onion/1. Single` | 3,000 | 18.40% | Bulb | Healthy | White | Single | BULB_GRADING |
| `2. Bulb/1. Healthy/2. White Onion/2. Multiple` | 1,110 | 6.81% | Bulb | Healthy | White | Multiple | BULB_GRADING |
| `2. Bulb/2. Unhealthy/1. Red Onion/1. Single` | 1,010 | 6.20% | Bulb | Unhealthy | Red | Single | BULB_GRADING |
| `2. Bulb/2. Unhealthy/1. Red Onion/2. Multiple` | 1,010 | 6.20% | Bulb | Unhealthy | Red | Multiple | BULB_GRADING |
| `2. Bulb/2. Unhealthy/2. White Onion/1. Single` | 1,010 | 6.20% | Bulb | Unhealthy | White | Single | BULB_GRADING |
| `2. Bulb/2. Unhealthy/2. White Onion/2. Multiple` | 1,010 | 6.20% | Bulb | Unhealthy | White | Multiple | BULB_GRADING |

---

## 4. Annotation Systems Audit

- **Bounding Box Labels**: None (`.txt`, `.xml`, `.json` missing).
- **Segmentation Masks**: None.
- **Classification Annotations**: Image-level label inferred solely from top-level directory names.
- **Annotation Type Finding**: `CLASSIFICATION_ONLY_DATASET`.
