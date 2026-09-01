import os
import time
import glob
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("SPOT_Storage_Cleanup")

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
TEMP_DIR = "/tmp"
MAX_AGE_SECONDS = 2 * 3600  # 2 Hours retention during hackathon judging

def cleanup_expired_raw_images():
    """
    Clears raw uploaded image files older than 2 hours to prevent disk bloat during judging.
    Database records in SQLite remain completely intact.
    """
    logger.info("Starting scheduled image storage cleanup (2-hour retention)...")
    deleted_count = 0
    freed_bytes = 0
    now = time.time()

    # Targets uploads directory and temporary image files
    targets = [
        os.path.join(UPLOAD_DIR, "*.jpg"),
        os.path.join(UPLOAD_DIR, "*.jpeg"),
        os.path.join(UPLOAD_DIR, "*.png"),
        os.path.join(UPLOAD_DIR, "*.webp"),
        os.path.join(TEMP_DIR, "spot_upload_*.jpg"),
        os.path.join(TEMP_DIR, "spot_upload_*.png"),
    ]

    # Ensure upload directory exists
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR, exist_ok=True)

    for pattern in targets:
        for file_path in glob.glob(pattern):
            try:
                file_age = now - os.path.getmtime(file_path)
                if file_age >= MAX_AGE_SECONDS:
                    file_size = os.path.getsize(file_path)
                    os.remove(file_path)
                    deleted_count += 1
                    freed_bytes += file_size
                    logger.info(f"Deleted expired raw image: {file_path} (Age: {file_age/3600:.1f}h)")
            except Exception as e:
                logger.error(f"Error removing {file_path}: {e}")

    freed_mb = freed_bytes / (1024 * 1024)
    logger.info(f"Cleanup completed. Removed {deleted_count} raw images, freed {freed_mb:.2f} MB of server storage.")
    return deleted_count, freed_mb

if __name__ == "__main__":
    cleanup_expired_raw_images()
