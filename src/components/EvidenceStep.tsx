import React from 'react';
import { useTranslation } from 'react-i18next';
import { ArrowLeft, ShieldCheck, Info, CheckCircle2, XCircle, AlertTriangle, Cpu } from 'lucide-react';
import { CanonicalInspectionResult } from '../types';

interface EvidenceStepProps {
  result: CanonicalInspectionResult;
  onBack: () => void;
}

function gradeToLabel(gradeName: string): 'HEALTHY' | 'DEFECTIVE' | 'REVIEW' {
  if (gradeName === 'Grade-A' || gradeName === 'A') return 'HEALTHY';
  if (gradeName === 'Grade-URS' || gradeName === 'URS') return 'REVIEW';
  return 'DEFECTIVE';
}

export const EvidenceStep: React.FC<EvidenceStepProps> = ({
  result,
  onBack,
}) => {
  const { t } = useTranslation();
  const gradeName = result.grading?.prototype_grade || 'Grade-A';
  const label = gradeToLabel(gradeName);
  const isHealthy = label === 'HEALTHY';
  const isReview = label === 'REVIEW';
  const confValue = typeof result.confidence === 'number' ? result.confidence : 0.95;
  const confPercent = (confValue * 100).toFixed(1);

  // Try to resolve captured image URL
  // Backend may return a relative path like /api/v1/... or a full URL
  const capturedImageUrl = result.captured_image_url;
  const hasImage = Boolean(capturedImageUrl);

  return (
    <div className="max-w-md mx-auto px-4 py-5 space-y-5 pb-24 font-sans text-[#163A2D]">
      {/* Header */}
      <div className="flex items-center gap-3">
        <button
          onClick={onBack}
          className="p-2 rounded-xl border border-[#163A2D]/15 bg-white text-[#163A2D] active:scale-95 transition-all shadow-2xs cursor-pointer"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div>
          <h1 className="text-xl font-black text-[#163A2D]">Visual Evidence</h1>
          <p className="text-xs text-[#163A2D]/70">Inspection: {result.inspection_id.slice(0, 16)}</p>
        </div>
      </div>

      {/* Captured Image OR placeholder */}
      <div className="bg-[#163A2D] rounded-3xl overflow-hidden aspect-4/3 relative flex items-center justify-center border-2 border-[#163A2D] shadow-md">
        {hasImage ? (
          <img
            src={capturedImageUrl!}
            alt="Captured Onion Sample"
            className="w-full h-full object-cover"
            onError={(e) => {
              // If image fails to load, hide it and show placeholder
              (e.currentTarget as HTMLImageElement).style.display = 'none';
              const placeholder = e.currentTarget.nextElementSibling as HTMLElement;
              if (placeholder) placeholder.style.display = 'flex';
            }}
          />
        ) : null}
        {/* Placeholder: shown when no image URL or image fails */}
        <div
          className="absolute inset-0 flex flex-col items-center justify-center p-6 text-center text-white space-y-2"
          style={{ display: hasImage ? 'none' : 'flex' }}
        >
          <ShieldCheck className="w-10 h-10 text-emerald-400" />
          <div className="text-xs font-black uppercase tracking-wider">Whole-Sample Optical Classifier</div>
          <p className="text-xs text-white/80 max-w-xs leading-relaxed">
            YOLO26n-cls classifies external onion characteristics across the entire sample image.
          </p>
        </div>

        {/* Classification badge overlay */}
        {hasImage && (
          <div className={`absolute top-3 right-3 px-3 py-1.5 rounded-full text-[10px] font-black uppercase flex items-center gap-1.5 border backdrop-blur-sm shadow-md ${
            isHealthy
              ? 'bg-emerald-600/90 text-white border-emerald-400'
              : isReview
              ? 'bg-amber-600/90 text-white border-amber-400'
              : 'bg-[#E51E3A]/90 text-white border-rose-400'
          }`}>
            {isHealthy
              ? <CheckCircle2 className="w-3.5 h-3.5" />
              : isReview
              ? <AlertTriangle className="w-3.5 h-3.5" />
              : <XCircle className="w-3.5 h-3.5" />
            }
            <span>{label}</span>
          </div>
        )}
      </div>

      {/* AI Assessment Card */}
      <div className="bg-white border border-[#163A2D]/15 rounded-3xl p-5 shadow-2xs space-y-4">
        <div className="flex items-center gap-2 border-b border-[#163A2D]/10 pb-3">
          <Cpu className="w-4 h-4 text-[#163A2D]/60" />
          <h2 className="text-xs font-black uppercase tracking-wider text-[#163A2D]">{t('aiAssessment')}</h2>
        </div>

        <div className="grid grid-cols-2 gap-3 text-xs">
          {/* Classification */}
          <div className="bg-[#F7F1E7] p-3 rounded-2xl border border-[#163A2D]/10">
            <div className="text-[#163A2D]/60 text-[10px] uppercase font-bold mb-1">Classification</div>
            <div className={`font-black text-sm ${
              isHealthy ? 'text-emerald-700' : isReview ? 'text-amber-700' : 'text-[#E51E3A]'
            }`}>
              {label}
            </div>
            <div className="text-[9px] text-[#163A2D]/50 mt-0.5">{gradeName}</div>
          </div>

          {/* Confidence */}
          <div className="bg-[#F7F1E7] p-3 rounded-2xl border border-[#163A2D]/10">
            <div className="text-[#163A2D]/60 text-[10px] uppercase font-bold mb-1">Confidence</div>
            <div className="font-black text-sm text-[#163A2D]">{confPercent}%</div>
            <div className="text-[9px] text-[#163A2D]/50 mt-0.5">Model score</div>
          </div>

          {/* Assessment Type */}
          <div className="bg-[#F7F1E7] p-3 rounded-2xl border border-[#163A2D]/10">
            <div className="text-[#163A2D]/60 text-[10px] uppercase font-bold mb-1">Assessment</div>
            <div className="font-bold text-[#163A2D] text-xs">{t('assessmentType')}</div>
            <div className="text-[9px] text-[#163A2D]/50 mt-0.5">External RGB optical</div>
          </div>

          {/* Model */}
          <div className="bg-[#F7F1E7] p-3 rounded-2xl border border-[#163A2D]/10">
            <div className="text-[#163A2D]/60 text-[10px] uppercase font-bold mb-1">Model</div>
            <div className="font-bold text-[#163A2D] text-xs">
              {result.model?.model_name || 'YOLO26n-cls'}
            </div>
            <div className="text-[9px] text-[#163A2D]/50 mt-0.5">
              {result.model?.source === 'real_model' ? 'Trained model' : result.model?.model_version || 'v1.0.0-pilot'}
            </div>
          </div>
        </div>
      </div>

      {/* Disclosure note */}
      <div className="p-4 bg-white border border-[#163A2D]/15 rounded-2xl flex items-start gap-3 shadow-2xs">
        <Info className="w-4 h-4 text-[#E51E3A] shrink-0 mt-0.5" />
        <p className="text-xs text-[#163A2D]/80 leading-relaxed font-medium">
          {t('classificationDisclaimer')}
        </p>
      </div>
    </div>
  );
};
