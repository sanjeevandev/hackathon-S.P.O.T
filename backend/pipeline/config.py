"""Configuration parameters for the S.P.O.T. Image Quality Gate.

DEVELOPMENT DEFAULTS ONLY:
The numerical threshold values defined in QualityGateConfig are baseline heuristics for initial
pipeline testing. They MUST later be calibrated against real APMC field images and official onion datasets.
Do NOT present these baseline values as scientifically validated final thresholds.
"""

from pydantic import BaseModel, Field


class QualityGateConfig(BaseModel):
    """Configurable thresholds for image quality screening."""

    minimum_width: int = Field(
        default=320,
        ge=64,
        description="Minimum acceptable image width in pixels. Development default."
    )
    minimum_height: int = Field(
        default=240,
        ge=64,
        description="Minimum acceptable image height in pixels. Development default."
    )
    blur_threshold: float = Field(
        default=50.0,
        ge=0.0,
        description="Laplacian variance threshold for blur screening (lower = blurrier). Heuristic default."
    )
    brightness_min: float = Field(
        default=40.0,
        ge=0.0,
        le=255.0,
        description="Minimum average pixel intensity (0-255). Images below this are rejected as underexposed."
    )
    brightness_max: float = Field(
        default=225.0,
        ge=0.0,
        le=255.0,
        description="Maximum average pixel intensity (0-255). Images above this are rejected as overexposed."
    )
    contrast_threshold: float = Field(
        default=20.0,
        ge=0.0,
        description="Minimum pixel intensity standard deviation (0-255). Images below this are low-contrast."
    )


class DatasetConfig(BaseModel):
    """Configurable dataset storage location."""

    dataset_dir: str = Field(
        default_factory=lambda: __import__("os").getenv("SPOT_DATASET_DIR", "/run/media/sanjeeva/0354-C3F0/ONION IQ"),
        description="Path to the authoritative onion dataset directory."
    )

