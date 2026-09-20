"""
S.P.O.T. held-out set manifest generator (labels explicit, hashes computed).

Creates the ground-truth manifest consumed by scripts/evaluate_models.py from a
directory of held-out images organised by label, so that the labels are explicit
and the checksums are computed rather than hand-written.

This script NEVER scores images and NEVER writes any results; it only records
files, their user-supplied labels, provenance, and measured SHA-256.

Usage:
  .venv/bin/python scripts/make_eval_manifest.py \
      --images artifacts/ml/v1_eval/images \
      --manifest artifacts/ml/v1_eval/manifest.csv \
      --source-note "independently gathered public onion-bulb images (not from this repo's datasets)"

Images can be placed either:
  * flat, with filenames prefixed `healthy_` or `defective_` (prefix is the label), or
  * in labelled subdirectories `healthy/` and `defective/` under --images.

Exit codes: 0 ok; 2 usage/label errors; 1 unexpected error.
"""

import argparse
import csv
import hashlib
import os
import sys

SUPPORTED_EXT = (".jpg", ".jpeg", ".png")


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def scan_label_suffixed(root: str) -> dict[str, str]:
    """Flat directory where the filename prefix encodes the label."""
    found: dict[str, str] = {}
    for name in sorted(os.listdir(root)):
        low = name.lower()
        if not low.endswith(SUPPORTED_EXT):
            continue
        if low.startswith("healthy_") or low.startswith("healthy-"):
            found[name] = "healthy"
        elif low.startswith("defective_") or low.startswith("defective-"):
            found[name] = "defective"
        else:
            sys.exit(f"Label error: flat-mode file {name!r} is not prefixed "
                     f"'healthy_' or 'defective_'. Use subdirectories or add the prefix.")
    return found


def scan_label_dirs(root: str) -> dict[str, str]:
    """Labelled subdirectories healthy/ and defective/."""
    found: dict[str, str] = {}
    present = [d for d in os.listdir(root)
               if os.path.isdir(os.path.join(root, d)) and d.lower() in ("healthy", "defective")]
    if not present:
        sys.exit(f"Label error: no healthy/ or defective/ subdirectory under {root}")
    for sub in present:
        sub_path = os.path.join(root, sub)
        for name in sorted(os.listdir(sub_path)):
            if not name.lower().endswith(SUPPORTED_EXT):
                continue
            found[os.path.join(sub, name)] = sub.lower()
    return found


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--images", required=True, help="Directory of held-out images")
    ap.add_argument("--manifest", required=True, help="Output manifest CSV path")
    ap.add_argument("--source-note", default="independently gathered public onion-bulb images (not from this repo's datasets)",
                    help="Provenance note recorded in every row")
    ap.add_argument("--mode", choices=["auto", "dirs", "flat"], default="auto",
                    help="Label discovery: auto (try dirs then flat), dirs (healthy//defective/ subdirs), flat (filename prefix)")
    args = ap.parse_args()

    if not os.path.isdir(args.images):
        print(f"FATAL: images directory not found: {args.images}", file=sys.stderr)
        return 2

    found: dict[str, str] = {}
    if args.mode == "dirs":
        found = scan_label_dirs(args.images)
    elif args.mode == "flat":
        found = scan_label_suffixed(args.images)
    else:  # auto
        try:
            found = scan_label_dirs(args.images)
        except SystemExit:
            found = scan_label_suffixed(args.images)

    if not found:
        print("FATAL: no supported images found", file=sys.stderr)
        return 2

    rows = []
    for rel, label in sorted(found.items()):
        path = os.path.join(args.images, rel)
        # `filename` is the path relative to --images, so a manifest generated
        # from labelled subdirectories round-trips against --images without
        # the caller needing to flatten anything.
        rows.append({
            "filename": rel.replace(os.sep, "/"),
            "subdir_note": (os.path.dirname(rel) if os.path.dirname(rel) != "" else ""),
            "class": label,
            "source_note": args.source_note,
            "checksum_sha256": sha256_file(path),
        })

    os.makedirs(os.path.dirname(os.path.abspath(args.manifest)), exist_ok=True)
    with open(args.manifest, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["filename", "subdir_note", "class", "source_note", "checksum_sha256"],
        )
        writer.writeheader()
        writer.writerows(rows)

    healthy = sum(1 for r in rows if r["class"] == "healthy")
    defective = sum(1 for r in rows if r["class"] == "defective")
    print(f"Wrote {args.manifest}: {len(rows)} images "
          f"(healthy={healthy}, defective={defective})")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit as e:
        raise
    except Exception as e:  # noqa: BLE001
        print(f"FATAL: {e}", file=sys.stderr)
        raise SystemExit(1)
