import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Sparkles, CheckCircle2, Loader2, Circle, AlertTriangle, RefreshCw, Camera, XCircle } from 'lucide-react';
import { NewInspectionMeta, CanonicalInspectionResult } from '../types';
import { uploadInspectionImage, getCanonicalResult } from '../api/inspections';

interface AnalyzingStepProps {
  meta: NewInspectionMeta;
  file: File;
  onSuccess: (result: CanonicalInspectionResult) => void;
  onError: (errorMsg: string) => void;
  onRetryScan?: () => void;
}

export const AnalyzingStep: React.FC<AnalyzingStepProps> = ({
  meta,
  file,
  onSuccess,
  onError,
  onRetryScan,
}) => {
  const { t } = useTranslation();
  const [currentStage, setCurrentStage] = useState<number>(1);
  const [pipelineError, setPipelineError] = useState<string | null>(null);
  const [isNotOnion, setIsNotOnion] = useState<boolean>(false);
  const [retakeReason, setRetakeReason] = useState<string | null>(null);
  const [reviewRequired, setReviewRequired] = useState<string | null>(null);
  const [imageUrl] = useState<string>(() => URL.createObjectURL(file));

  const stages = [
    { id: 1, label: t('stage1') },
    { id: 2, label: 'Onion Domain Validation Gate' },
    { id: 3, label: t('stage2') },
    { id: 4, label: t('stage3') },
    { id: 5, label: t('stage4') },
  ];

  const executePipeline = async () => {
    setPipelineError(null);
    setIsNotOnion(false);
    setRetakeReason(null);
    setReviewRequired(null);
    setCurrentStage(1);

    try {
      setTimeout(() => setCurrentStage(2), 250);

      const uploadRes = await uploadInspectionImage({
        file,
        batchId: meta.batch_id,
        centerId: meta.procurement_center_id,
      });

      // 1. Low-confidence classification → route to explicit review, with the
      // classification preserved in the response for the inspector to weigh.
      if (uploadRes.status === 'REVIEW_REQUIRED' || uploadRes.vision_result?.status === 'LOW_CONFIDENCE') {
        const conf = uploadRes.vision_result?.overall_confidence;
        const confText = typeof conf === 'number' ? ` (confidence ${(conf * 100).toFixed(0)}%)` : '';
        setReviewRequired(
          uploadRes.error_message
            ? `${uploadRes.error_message}${confText}`
            : `Model classified this image with low confidence${confText}. Please review before finalizing grading.`
        );
        return;
      }

      // 2. Check Onion Validation Gate Result
      if (
        uploadRes.status === 'REJECTED_NOT_ONION' ||
        uploadRes.quality_gate?.status === 'REJECTED_NOT_ONION' ||
        uploadRes.quality_gate?.reasons?.includes('NOT_AN_ONION')
      ) {
        setIsNotOnion(true);
        return;
      }

      // 3. Check Quality Gate Retake Result (Blur/Dark/Resolution)
      if (
        uploadRes.status === 'RETAKE_REQUIRED' ||
        uploadRes.quality_gate?.status === 'RETAKE_REQUIRED' ||
        uploadRes.quality_gate?.passed === false
      ) {
        const reasonText =
          uploadRes.quality_gate?.recommendations?.[0] ||
          uploadRes.quality_gate?.reasons?.join(', ') ||
          'Image quality insufficient for accurate quality grading.';
        setRetakeReason(reasonText);
        return;
      }

      setCurrentStage(3);
      setTimeout(() => setCurrentStage(4), 350);

      const rawId = uploadRes.inspection_id || uploadRes.request_id || meta.batch_id;
      const inspectionId = rawId.startsWith('INSP-') ? rawId : (rawId.startsWith('REQ-') ? `INSP-${rawId}` : rawId);
      const result = await getCanonicalResult(inspectionId);

      setCurrentStage(5);

      setTimeout(() => {
        onSuccess(result);
      }, 400);
    } catch (err: any) {
      if (err.message && err.message.toLowerCase().includes('onion')) {
        setIsNotOnion(true);
      } else {
        setPipelineError(err.message || 'Inspection failed. Please check backend connection.');
      }
    }
  };

  useEffect(() => {
    executePipeline();

    return () => {
      URL.revokeObjectURL(imageUrl);
    };
  }, []);

  // SCREEN: NON-ONION REJECTION STATE
  if (isNotOnion) {
    return (
      <div className="max-w-md mx-auto px-4 py-6 space-y-5 text-center pb-24 font-sans text-[#163A2D] animate-in fade-in">
        {/* Rejection Header */}
        <div className="space-y-1.5">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-rose-100 text-[#E51E3A] border border-[#E51E3A]/20 rounded-full text-[10px] font-black uppercase tracking-wider shadow-2xs">
            <XCircle className="w-3.5 h-3.5" />
            <span>Validation Gate</span>
          </div>
          <h1 className="text-2xl font-black text-[#163A2D]">Scan onion only</h1>
          <p className="text-xs text-[#163A2D]/80 font-bold">
            Please place one onion inside the camera frame.
          </p>
        </div>

        {/* Thumbnail of Rejected Image */}
        <div className="relative w-44 h-44 mx-auto rounded-3xl overflow-hidden shadow-md border-3 border-[#E51E3A] bg-[#163A2D]">
          <img
            src={imageUrl}
            alt="Rejected Non-Onion Input"
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-[#E51E3A]/20 backdrop-grayscale flex items-center justify-center">
            <span className="bg-[#E51E3A] text-white px-2.5 py-1 rounded-full text-[9px] font-black uppercase tracking-widest shadow-md">
              Rejected
            </span>
          </div>
        </div>

        {/* Reason Card */}
        <div className="p-4 bg-white border border-[#E51E3A]/30 rounded-3xl text-left space-y-2.5 shadow-2xs">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-[#E51E3A] shrink-0" />
            <h4 className="text-xs font-black uppercase text-[#E51E3A]">
              Quality Analysis Blocked
            </h4>
          </div>
          <p className="text-[11px] text-[#163A2D]/80 font-medium leading-relaxed">
            The input image was rejected before quality inference. YOLO26 binary classifier is specifically calibrated for onion health and defect grading and is not a generic object detector.
          </p>
        </div>

        {/* Action Controls */}
        <div className="space-y-2 pt-1">
          <button
            onClick={() => {
              if (onRetryScan) {
                onRetryScan();
              } else {
                onError('Return to camera');
              }
            }}
            className="w-full min-h-[48px] py-3 px-4 bg-[#E51E3A] hover:bg-[#c91530] text-white rounded-2xl font-black shadow-md active:scale-95 transition-all flex items-center justify-center gap-2 text-xs uppercase tracking-wider cursor-pointer"
          >
            <Camera className="w-4 h-4" />
            <span>Scan Again</span>
          </button>

          <button
            onClick={() => onError('Cancelled')}
            className="w-full py-2.5 px-4 bg-white text-[#163A2D] border border-[#163A2D]/15 hover:bg-[#F7F1E7] rounded-xl text-xs font-bold active:scale-95 transition-all cursor-pointer"
          >
            <span>{t('home')}</span>
          </button>
        </div>
      </div>
    );
  }

  // SCREEN: RETAKE REQUIRED STATE (Blur/Dark/Low Res)
  if (retakeReason) {
    return (
      <div className="max-w-md mx-auto px-4 py-6 space-y-5 text-center pb-24 font-sans text-[#163A2D] animate-in fade-in">
        <div className="space-y-1.5">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-amber-100 text-amber-900 border border-amber-300 rounded-full text-[10px] font-black uppercase tracking-wider shadow-2xs">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-700" />
            <span>Quality Gate</span>
          </div>
          <h1 className="text-2xl font-black text-[#163A2D]">Retake Required</h1>
          <p className="text-xs text-[#163A2D]/80 font-medium">
            {retakeReason}
          </p>
        </div>

        <div className="relative w-44 h-44 mx-auto rounded-3xl overflow-hidden shadow-md border-3 border-amber-500 bg-[#163A2D]">
          <img
            src={imageUrl}
            alt="Sample preview"
            className="w-full h-full object-cover opacity-80"
          />
        </div>

        <div className="space-y-2 pt-1">
          <button
            onClick={() => {
              if (onRetryScan) onRetryScan();
              else onError('Retake requested');
            }}
            className="w-full min-h-[48px] py-3 px-4 bg-[#E51E3A] hover:bg-[#c91530] text-white rounded-2xl font-black shadow-md active:scale-95 transition-all flex items-center justify-center gap-2 text-xs uppercase tracking-wider cursor-pointer"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Retake Photo</span>
          </button>

          <button
            onClick={() => onError('Cancelled')}
            className="w-full py-2.5 px-4 bg-white text-[#163A2D] border border-[#163A2D]/15 hover:bg-[#F7F1E7] rounded-xl text-xs font-bold active:scale-95 transition-all cursor-pointer"
          >
            <span>{t('home')}</span>
          </button>
        </div>
      </div>
    );
  }

  // SCREEN: LOW-CONFIDENCE REVIEW STATE (model ran, but below accept threshold)
  if (reviewRequired) {
    return (
      <div className="max-w-md mx-auto px-4 py-6 space-y-5 text-center pb-24 font-sans text-[#163A2D] animate-in fade-in">
        <div className="space-y-1.5">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-amber-100 text-amber-900 border border-amber-300 rounded-full text-[10px] font-black uppercase tracking-wider shadow-2xs">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-700" />
            <span>Human Review</span>
          </div>
          <h1 className="text-2xl font-black text-[#163A2D]">Review Required</h1>
          <p className="text-xs text-[#163A2D]/80 font-medium">
            The model was not confident enough to auto-grade this onion.
          </p>
        </div>

        <div className="relative w-44 h-44 mx-auto rounded-3xl overflow-hidden shadow-md border-3 border-amber-500 bg-[#163A2D]">
          <img
            src={imageUrl}
            alt="Sample preview"
            className="w-full h-full object-cover"
          />
        </div>

        <div className="p-4 bg-white border border-amber-500/40 rounded-3xl text-left shadow-2xs">
          <p className="text-[11px] text-[#163A2D]/80 font-medium leading-relaxed">
            {reviewRequired}
          </p>
        </div>

        <div className="space-y-2 pt-1">
          <button
            onClick={() => {
              if (onRetryScan) onRetryScan();
              else onError('Return to camera');
            }}
            className="w-full min-h-[48px] py-3 px-4 bg-[#E51E3A] hover:bg-[#c91530] text-white rounded-2xl font-black shadow-md active:scale-95 transition-all flex items-center justify-center gap-2 text-xs uppercase tracking-wider cursor-pointer"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Retake Photo</span>
          </button>

          <button
            onClick={() => onError('Cancelled')}
            className="w-full py-2.5 px-4 bg-white text-[#163A2D] border border-[#163A2D]/15 hover:bg-[#F7F1E7] rounded-xl text-xs font-bold active:scale-95 transition-all cursor-pointer"
          >
            <span>{t('home')}</span>
          </button>
        </div>
      </div>
    );
  }

  // SCREEN: SCANNING / ANALYZING IN PROGRESS
  return (
    <div className="max-w-md mx-auto px-4 py-6 space-y-6 text-center pb-24 font-sans text-[#163A2D]">
      {/* Title */}
      <div className="space-y-1.5">
        <div className="inline-flex items-center gap-1.5 px-3 py-0.5 bg-white border border-[#163A2D]/15 text-[#163A2D] rounded-full text-[10px] font-black uppercase tracking-wider shadow-2xs">
          <Sparkles className="w-3.5 h-3.5 text-[#E51E3A]" />
          <span>{t('opticalAiGrading')}</span>
        </div>
        <h1 className="text-2xl font-black text-[#163A2D]">{t('analyzingTitle')}</h1>
        <p className="text-xs text-[#163A2D]/70 font-medium">
          {t('analyzingSubtitle')}
        </p>
      </div>

      {/* Captured Image Preview with Scanning Frame */}
      <div className="relative w-44 h-44 mx-auto rounded-3xl overflow-hidden shadow-md border-3 border-[#163A2D] bg-[#163A2D]">
        <img
          src={imageUrl}
          alt="Inspecting Onion"
          className="w-full h-full object-cover"
        />
        {/* Animated Scanning Laser Line */}
        {!pipelineError && (
          <div className="absolute left-0 right-0 h-1 bg-[#E51E3A] shadow-[0_0_12px_#E51E3A] animate-bounce" />
        )}
      </div>

      {/* Pipeline Error State */}
      {pipelineError ? (
        <div className="p-4 bg-white border-2 border-[#E51E3A] rounded-2xl text-left space-y-3 shadow-md">
          <div className="flex items-start gap-2.5">
            <AlertTriangle className="w-5 h-5 text-[#E51E3A] shrink-0 mt-0.5" />
            <div>
              <h4 className="text-xs font-black uppercase text-[#E51E3A]">{t('backendOffline')}</h4>
              <p className="text-[11px] text-[#163A2D]/80 mt-1 font-medium leading-relaxed">
                {pipelineError}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 pt-1">
            <button
              onClick={executePipeline}
              className="flex-1 py-2.5 bg-[#E51E3A] hover:bg-[#c91530] text-white rounded-xl text-xs font-black uppercase flex items-center justify-center gap-1.5 shadow-md active:scale-95 transition-all cursor-pointer"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>{t('retryConnection')}</span>
            </button>
            <button
              onClick={() => onError(pipelineError)}
              className="px-3 py-2.5 bg-[#F7F1E7] text-[#163A2D] rounded-xl text-xs font-bold border border-[#163A2D]/20 active:scale-95 cursor-pointer"
            >
              <span>{t('home')}</span>
            </button>
          </div>
        </div>
      ) : (
        /* Progress Stages Checklist */
        <div className="bg-white border border-[#163A2D]/15 rounded-3xl p-5 shadow-2xs space-y-3 text-left">
          {stages.map((stage) => {
            const isDone = currentStage > stage.id;
            const isCurrent = currentStage === stage.id;
            return (
              <div key={stage.id} className="flex items-center gap-3">
                {isDone ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                ) : isCurrent ? (
                  <Loader2 className="w-4 h-4 text-[#E51E3A] animate-spin shrink-0" />
                ) : (
                  <Circle className="w-4 h-4 text-[#163A2D]/30 shrink-0" />
                )}
                <span
                  className={`text-xs ${
                    isDone
                      ? 'text-[#163A2D]/50 line-through'
                      : isCurrent
                      ? 'text-[#163A2D] font-black'
                      : 'text-[#163A2D]/40'
                  }`}
                >
                  {stage.label}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
