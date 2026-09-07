"""Image Quality Gate for screening unusable images before vision inference.

Screening metrics evaluated:
1. Resolution validation (minimum width and height check)
2. Blur detection (Laplacian variance threshold)
3. Exposure analysis (minimum and maximum average pixel brightness check)
4. Contrast check (pixel intensity standard deviation)

If any check fails, the gate returns RETAKE_REQUIRED with explicit reason codes and guidance recommendations.
"""

import io
import time
from typing import Tuple, List, Optional
import numpy as np
from PIL import Image

try:
    import cv2
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False

from backend.pipeline.config import QualityGateConfig
from backend.pipeline.schemas import QualityGateResult, QualityGateMetrics


class ImageQualityGate:
    """Deterministic image quality gate evaluator."""

    def __init__(self, config: Optional[QualityGateConfig] = None):
        self.config = config or QualityGateConfig()

    def _compute_metrics(self, image_bytes: bytes) -> Tuple[QualityGateMetrics, Image.Image]:
        """Calculates image dimension, blur variance, brightness, and contrast metrics."""
        pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        width, height = pil_img.size

        np_img = np.array(pil_img)
        gray = np.array(pil_img.convert("L"))

        # Brightness & Contrast
        brightness = float(np.mean(gray))
        contrast = float(np.std(gray))

        # Blur score via Laplacian variance
        if HAS_OPENCV:
            blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        else:
            # Fallback Laplacian implementation using numpy if cv2 missing
            kernel = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]], dtype=np.float64)
            from scipy.signal import convolve2d
            lap = convolve2d(gray.astype(np.float64), kernel, mode="valid")
            blur_score = float(lap.var())

        metrics = QualityGateMetrics(
            blur_score=round(blur_score, 2),
            brightness=round(brightness, 2),
            contrast=round(contrast, 2),
            width=width,
            height=height
        )

        return metrics, pil_img

    def evaluate(self, image_bytes: bytes) -> QualityGateResult:
        """Evaluates input image against configured quality thresholds.

        Returns:
            QualityGateResult containing status ('PASS' or 'RETAKE_REQUIRED'),
            reasons list, objective metrics, and actionable recommendations.
        """
        metrics, _ = self._compute_metrics(image_bytes)
        reasons: List[str] = []
        recommendations: List[str] = []

        # 1. Resolution Check
        if metrics.width < self.config.minimum_width or metrics.height < self.config.minimum_height:
            reasons.append("IMAGE_RESOLUTION_TOO_LOW")
            recommendations.append(
                f"Image resolution ({metrics.width}x{metrics.height}) is below minimum requirement "
                f"({self.config.minimum_width}x{self.config.minimum_height}). Capture at higher resolution."
            )

        # 2. Blur Detection
        if metrics.blur_score < self.config.blur_threshold:
            reasons.append("IMAGE_TOO_BLURRY")
            recommendations.append("Hold the phone steady and tap to focus on the onion bulb batch.")

        # 3. Brightness / Exposure Check
        if metrics.brightness < self.config.brightness_min:
            reasons.append("IMAGE_TOO_DARK")
            recommendations.append("Increase surrounding illumination or enable flash for better visibility.")
        elif metrics.brightness > self.config.brightness_max:
            reasons.append("IMAGE_TOO_BRIGHT")
            recommendations.append("Avoid direct harsh sunlight glare on the onions.")

        # 4. Contrast Check
        if metrics.contrast < self.config.contrast_threshold:
            reasons.append("IMAGE_LOW_CONTRAST")
            recommendations.append("Ensure onions are positioned clearly against a neutral background surface.")

        passed = len(reasons) == 0
        status = "PASS" if passed else "RETAKE_REQUIRED"

        if passed:
            recommendations.append("Image quality is optimal for vision analysis.")

        return QualityGateResult(
            status=status,
            passed=passed,
            reasons=reasons,
            metrics=metrics,
            recommendations=recommendations
        )
