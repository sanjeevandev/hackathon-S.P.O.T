import os
import sys
import json
import time
import datetime
from backend.ai.annotation.workstation import AnnotationWorkstationManager

start_time = time.time()
print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Step 1: Initializing Annotation Workstation Manager...")

manager = AnnotationWorkstationManager()

# Load queue & progress
queue = manager.get_queue("HUMAN_ANNOTATOR_01")
progress = manager.get_progress("HUMAN_ANNOTATOR_01")

print(f"Loaded Work Queue Size: {progress['total_images']} images.")
print(f"Completed Human Annotations: {progress['completed']}")
print(f"Remaining Images: {progress['remaining']}")
print(f"Needs Review: {progress['needs_review']}")

# Test deterministic export
json_export = manager.export_annotations(format="json")
csv_export = manager.export_annotations(format="csv")

print(f"Exported JSON to: {json_export}")
print(f"Exported CSV to: {csv_export}")
print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Workstation Verification completed in {time.time()-start_time:.2f}s!")
