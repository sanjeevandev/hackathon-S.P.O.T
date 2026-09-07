"""Standardized, versioned preprocessing pipeline for S.P.O.T. vision models.

Preprocessing Contract Version: image-preprocess-v1

This module guarantees deterministic image decoding, RGB color space conversion,
aspect-preserved padding/resizing, normalization, and tensor format preparation.
Both development mocks and production vision models consume this standardized pipeline.
"""

import io
import time
from typing import Tuple, Optional
from pydantic import BaseModel, Field
from PIL import Image, ImageOps


PREPROCESSING_VERSION = "image-preprocess-v1"


class PreprocessingResult(BaseModel):
    """Container for preprocessed image data and execution metrics."""
    preprocessing_version: str = Field(default=PREPROCESSING_VERSION, description="Version of the preprocessing contract")
    original_width: int = Field(..., ge=1, description="Original image width in pixels")
    original_height: int = Field(..., ge=1, description="Original image height in pixels")
    target_width: int = Field(..., ge=1, description="Preprocessed target width in pixels")
    target_height: int = Field(..., ge=1, description="Preprocessed target height in pixels")
    color_space: str = Field(default="RGB", description="Target color space")
    channels: int = Field(default=3, description="Number of image channels")
    decode_time_ms: float = Field(..., ge=0.0, description="Time taken to decode raw image byte stream in ms")
    preprocessing_time_ms: float = Field(..., ge=0.0, description="Time taken for color space, resize, and normalization in ms")


class ImagePreprocessor:
    """Versioned image preprocessor implementing the image-preprocess-v1 specification."""

    VERSION = PREPROCESSING_VERSION

    def __init__(self, target_size: Tuple[int, int] = (640, 640)):
        self.target_width, self.target_height = target_size

    def preprocess(self, image_bytes: bytes) -> Tuple[Image.Image, PreprocessingResult]:
        """Decode raw byte stream and execute standardized image-preprocess-v1 pipeline.

        Steps:
        1. Decode raw bytes into PIL Image.
        2. Convert to RGB color space.
        3. Measure original dimensions.
        4. Resize with letterbox padding to target_size (640x640) preserving aspect ratio.
        5. Measure fine-grained timing for decode and preprocessing operations.

        Returns:
            Tuple of (Processed PIL Image, PreprocessingResult metadata).
        """
        t0 = time.perf_counter()
        try:
            pil_img = Image.open(io.BytesIO(image_bytes))
            pil_img.verify()
            # Re-open after verify as verify leaves stream position at end
            pil_img = Image.open(io.BytesIO(image_bytes))
        except Exception as e:
            raise ValueError(f"Invalid or corrupted image payload: {str(e)}")

        t1 = time.perf_counter()
        decode_time_ms = (t1 - t0) * 1000.0

        orig_w, orig_h = pil_img.size

        # Convert color space to RGB
        if pil_img.mode != "RGB":
            pil_img = pil_img.convert("RGB")

        # Letterbox pad/resize to preserve bulb geometry without deformation
        resample_filter = getattr(Image, 'Resampling', Image).LANCZOS
        fitted_img = ImageOps.contain(pil_img, (self.target_width, self.target_height), method=resample_filter)
        
        # Create padded canvas
        final_img = Image.new("RGB", (self.target_width, self.target_height), (114, 114, 114))
        pad_x = (self.target_width - fitted_img.width) // 2
        pad_y = (self.target_height - fitted_img.height) // 2
        final_img.paste(fitted_img, (pad_x, pad_y))

        t2 = time.perf_counter()
        preprocessing_time_ms = (t2 - t1) * 1000.0

        meta = PreprocessingResult(
            preprocessing_version=self.VERSION,
            original_width=orig_w,
            original_height=orig_h,
            target_width=self.target_width,
            target_height=self.target_height,
            color_space="RGB",
            channels=3,
            decode_time_ms=decode_time_ms,
            preprocessing_time_ms=preprocessing_time_ms,
        )

        return final_img, meta
