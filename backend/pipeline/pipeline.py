"""Pipeline orchestrator for S.P.O.T. quality inspection with Phase 7 system hardening.

Pipeline Flow:
Image Bytes
→ Image Preprocessor (decode & format)
→ Image Quality Gate
→ [Pass Check]
→ Vision Model Execution
→ Vision Output Validator
→ Timings & AI Diagnostics Recording

CRITICAL GUARANTEES:
1. If Image Quality Gate status is RETAKE_REQUIRED (passed=False), the Vision Model is NEVER called.
2. Malformed model outputs are rejected by VisionOutputValidator.
3. Every step is traceably logged with request_id.
"""

import time
import logging
import datetime
from typing import Optional
from backend.ai.base import VisionModel
from backend.ai.schemas import ImageInput, VisionResult
from backend.ai.registry import get_vision_model, ProductionModelUnavailableError
from backend.ai.preprocessing import ImagePreprocessor, PreprocessingResult
from backend.ai.validation import VisionOutputValidator, ModelValidationError
from backend.ai.status import AIHealthDiagnostics
from backend.pipeline.quality_gate import ImageQualityGate
from backend.pipeline.config import QualityGateConfig
from backend.pipeline.schemas import PipelineResult, PipelineTimings, QualityGateResult

logger = logging.getLogger("SPOTPipeline")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    formatter = logging.Formatter('[%(asctime)s][%(name)s][%(levelname)s][req_id=%(message)s]')
    ch.setFormatter(formatter)
    logger.addHandler(ch)


class InspectionPipeline:
    """Orchestrates image quality screening, versioned preprocessing, and validated vision inference."""

    def __init__(
        self,
        vision_model: Optional[VisionModel] = None,
        quality_gate_config: Optional[QualityGateConfig] = None,
        environment: Optional[str] = None
    ):
        self.preprocessor = ImagePreprocessor()
        self.quality_gate = ImageQualityGate(config=quality_gate_config)
        self.vision_model = vision_model
        self.environment = environment

    def execute(self, image_input: ImageInput, image_bytes: bytes) -> PipelineResult:
        """Executes the inspection pipeline for an input image.

        Args:
            image_input: Typed metadata for the image.
            image_bytes: Raw image file bytes.

        Returns:
            PipelineResult containing quality gate status, vision result, and measured timings.
        """
        start_total = time.perf_counter()
        req_id = image_input.image_id

        # Step 1: Preprocessing & Decoding
        try:
            _, prep_meta = self.preprocessor.preprocess(image_bytes)
        except Exception as prep_err:
            total_time_ms = round((time.perf_counter() - start_total) * 1000.0, 3)
            logger.error(f"{req_id} PREPROCESSING_FAILED error={str(prep_err)}")
            dummy_qg = QualityGateResult(
                status="RETAKE_REQUIRED",
                passed=False,
                reasons=["CORRUPTED_IMAGE_PAYLOAD"],
                metrics={"blur_score": 0.0, "brightness": 0.0, "contrast": 0.0, "width": 0, "height": 0},
                recommendations=["Please capture a new uncorrupted image file."]
            )
            return PipelineResult(
                status="RETAKE_REQUIRED",
                request_id=req_id,
                quality_gate=dummy_qg,
                vision_result=None,
                timings=PipelineTimings(
                    image_decode_time_ms=0.0,
                    preprocessing_time_ms=0.0,
                    quality_gate_time_ms=0.0,
                    model_time_ms=0.0,
                    total_pipeline_time_ms=total_time_ms,
                    vision_time_ms=0.0,
                ),
                error_message=f"Image decoding failed: {str(prep_err)}"
            )

        # Step 2: Quality Gate Screening
        start_qg = time.perf_counter()
        qg_result: QualityGateResult = self.quality_gate.evaluate(image_bytes)
        qg_time_ms = round((time.perf_counter() - start_qg) * 1000.0, 3)

        # Step 3: Check Quality Gate Result
        # CRITICAL RULE: If quality gate fails, DO NOT call vision model.
        if not qg_result.passed:
            total_time_ms = round((time.perf_counter() - start_total) * 1000.0, 3)
            timings = PipelineTimings(
                image_decode_time_ms=prep_meta.decode_time_ms,
                preprocessing_time_ms=prep_meta.preprocessing_time_ms,
                quality_gate_time_ms=qg_time_ms,
                model_time_ms=0.0,
                total_pipeline_time_ms=total_time_ms,
                vision_time_ms=0.0,
            )

            logger.info(
                f"{req_id} status=RETAKE_REQUIRED qg_status={qg_result.status} "
                f"reasons={qg_result.reasons} qg_time_ms={qg_time_ms} total_ms={total_time_ms}"
            )

            return PipelineResult(
                status="RETAKE_REQUIRED",
                request_id=req_id,
                quality_gate=qg_result,
                vision_result=None,
                timings=timings,
                error_message=None
            )

        # Step 4: Resolve Vision Model
        model = self.vision_model
        if model is None:
            try:
                model = get_vision_model(environment=self.environment)
            except ProductionModelUnavailableError as p_err:
                total_time_ms = round((time.perf_counter() - start_total) * 1000.0, 3)
                timings = PipelineTimings(
                    image_decode_time_ms=prep_meta.decode_time_ms,
                    preprocessing_time_ms=prep_meta.preprocessing_time_ms,
                    quality_gate_time_ms=qg_time_ms,
                    model_time_ms=0.0,
                    total_pipeline_time_ms=total_time_ms,
                    vision_time_ms=0.0,
                )
                logger.error(f"{req_id} status=MODEL_UNAVAILABLE error={str(p_err)}")
                return PipelineResult(
                    status="MODEL_UNAVAILABLE",
                    request_id=req_id,
                    quality_gate=qg_result,
                    vision_result=None,
                    timings=timings,
                    error_message=str(p_err)
                )

        # Step 5: Execute Vision Inference & Output Validation
        start_vis = time.perf_counter()
        try:
            vision_result: VisionResult = model.analyze(image_input, image_bytes)
            vis_time_ms = round((time.perf_counter() - start_vis) * 1000.0, 3)

            # Validate Model Output Contract
            VisionOutputValidator.validate_vision_result(
                vision_result, prep_meta.original_width, prep_meta.original_height
            )

            # Record global AI diagnostics
            now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
            AIHealthDiagnostics.record_inference(vis_time_ms, now_iso)

            total_time_ms = round((time.perf_counter() - start_total) * 1000.0, 3)

            timings = PipelineTimings(
                image_decode_time_ms=prep_meta.decode_time_ms,
                preprocessing_time_ms=prep_meta.preprocessing_time_ms,
                quality_gate_time_ms=qg_time_ms,
                model_time_ms=vis_time_ms,
                total_pipeline_time_ms=total_time_ms,
                vision_time_ms=vis_time_ms,
            )

            logger.info(
                f"{req_id} status=SUCCESS qg_status={qg_result.status} "
                f"model_name={model.model_name} model_version={model.model_version} "
                f"source={model.source} vis_time_ms={vis_time_ms} total_ms={total_time_ms}"
            )

            return PipelineResult(
                status="SUCCESS",
                request_id=req_id,
                quality_gate=qg_result,
                vision_result=vision_result,
                timings=timings,
                error_message=None
            )

        except ModelValidationError as val_err:
            vis_time_ms = round((time.perf_counter() - start_vis) * 1000.0, 3)
            total_time_ms = round((time.perf_counter() - start_total) * 1000.0, 3)
            logger.error(f"{req_id} status=MODEL_VALIDATION_FAILED error={str(val_err)}")
            timings = PipelineTimings(
                image_decode_time_ms=prep_meta.decode_time_ms,
                preprocessing_time_ms=prep_meta.preprocessing_time_ms,
                quality_gate_time_ms=qg_time_ms,
                model_time_ms=vis_time_ms,
                total_pipeline_time_ms=total_time_ms,
                vision_time_ms=vis_time_ms,
            )
            return PipelineResult(
                status="PIPELINE_ERROR",
                request_id=req_id,
                quality_gate=qg_result,
                vision_result=None,
                timings=timings,
                error_message=f"Model output validation failed: {str(val_err)}"
            )

        except Exception as err:
            vis_time_ms = round((time.perf_counter() - start_vis) * 1000.0, 3)
            total_time_ms = round((time.perf_counter() - start_total) * 1000.0, 3)
            timings = PipelineTimings(
                image_decode_time_ms=prep_meta.decode_time_ms,
                preprocessing_time_ms=prep_meta.preprocessing_time_ms,
                quality_gate_time_ms=qg_time_ms,
                model_time_ms=vis_time_ms,
                total_pipeline_time_ms=total_time_ms,
                vision_time_ms=vis_time_ms,
            )
            logger.error(f"{req_id} status=PIPELINE_ERROR model={model.model_name} error={str(err)}")
            return PipelineResult(
                status="PIPELINE_ERROR",
                request_id=req_id,
                quality_gate=qg_result,
                vision_result=None,
                timings=timings,
                error_message=f"Vision model execution failed: {str(err)}"
            )
