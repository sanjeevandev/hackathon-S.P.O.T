import React from 'react';
import { useTranslation } from 'react-i18next';
import {
  FileText,
  Eye,
  RefreshCw,
  Info,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Clock,
  Hash,
  Cpu,
} from 'lucide-react';
import { CanonicalInspectionResult, AppRoute } from '../types';

interface ResultStepProps {
  result: CanonicalInspectionResult;
  onNavigate: (route: AppRoute) => void;
  onNewInspection: () => void;
}

/** Maps internal grade codes to user-facing HEALTHY / DEFECTIVE */
function gradeToLabel(gradeName: string): 'HEALTHY' | 'DEFECTIVE' | 'REVIEW' {
  if (gradeName === 'Grade-A' || gradeName === 'A') return 'HEALTHY';
  if (gradeName === 'Grade-URS' || gradeName === 'URS') return 'REVIEW';
  return 'DEFECTIVE';
}

export const ResultStep: React.FC<ResultStepProps> = ({
  result,
  onNavigate,
  onNewInspection,
}) => {
  const { t } = useTranslation();
  const {
    status,
    grading,
    batch_statistics: stats,
    explanation,
    confidence,
    inspection_id,
    batch_id,
  } = result;

  // 1. RETAKE REQUIRED STATE
  if (status === 'RETAKE_REQUIRED' || result.image_quality?.quality_status === 'RETAKE_REQUIRED') {
    return (
      <div className="max-w-md mx-auto px-4 py-8 space-y-6 pb-24 font-sans text-[#163A2D]">
        <div className="bg-white border-2 border-[#E51E3A] rounded-3xl p-6 shadow-md text-center space-y-4">
          <div className="w-14 h-14 bg-[#F7F1E7] text-[#E51E3A] rounded-full flex items-center justify-center mx-auto">
            <AlertTriangle className="w-8 h-8" />
          </div>
          <div className="space-y-1">
            <h2 className="text-xl font-black text-[#163A2D]">IMAGE RETAKE REQUIRED</h2>
            <p className="text-xs text-[#163A2D]/70 font-medium">Quality screening flagged insufficient lighting or blur.</p>
          </div>

          <div className="bg-[#F7F1E7] border border-[#163A2D]/10 rounded-2xl p-4 text-left space-y-2 text-xs text-[#163A2D]">
            <div className="font-bold text-[#163A2D]">Recommendations:</div>
            <ul className="list-disc pl-4 space-y-1 text-[#163A2D]/80">
              {explanation?.limitations?.map((lim, idx) => (
                <li key={idx}>{lim}</li>
              )) || <li>Ensure single onion is centered with good lighting.</li>}
            </ul>
          </div>

          <button
            onClick={onNewInspection}
            className="w-full py-3.5 px-4 bg-[#E51E3A] hover:bg-[#c91530] text-white rounded-2xl font-black shadow-md active:scale-95 transition-all flex items-center justify-center gap-2 text-xs uppercase cursor-pointer"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Retake Photo</span>
          </button>
        </div>
      </div>
    );
  }

  const gradeName = grading?.prototype_grade || 'Grade-A';
  const label = gradeToLabel(gradeName);
  const isHealthy = label === 'HEALTHY';
  const isReview = label === 'REVIEW';
  const confValue = typeof confidence === 'number' ? confidence : 0.95;
  const confPercent = Math.round(confValue * 100);

  // Check if defect flags are meaningful (binary classifier may return all zeros)
  const hasAnyDefects = stats && (
    stats.damaged_count > 0 ||
    stats.rotten_count > 0 ||
    stats.sprouted_count > 0 ||
    stats.undersized_count > 0
  );

  return (
    <div className="max-w-md mx-auto px-4 py-5 space-y-4 pb-28 font-sans text-[#163A2D]">

      {/* Quality Result Hero Card */}
      <div className={`rounded-3xl p-6 shadow-md text-center space-y-4 border-2 ${
        isHealthy
          ? 'bg-emerald-50 border-emerald-200'
          : isReview
          ? 'bg-amber-50 border-amber-200'
          : 'bg-rose-50 border-[#E51E3A]/30'
      }`}>
        {/* QUALITY RESULT Label */}
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-wider bg-white/80 border border-[#163A2D]/10 shadow-2xs">
          <Cpu className="w-3 h-3 text-[#163A2D]/70" />
          <span className="text-[#163A2D]">{t('qualityResult')}</span>
        </div>

        {/* Primary HEALTHY / DEFECTIVE Headline */}
        <div className="space-y-2">
          <div className="flex items-center justify-center gap-3">
            {isHealthy ? (
              <CheckCircle2 className="w-8 h-8 text-emerald-600 shrink-0" />
            ) : isReview ? (
              <AlertTriangle className="w-8 h-8 text-amber-600 shrink-0" />
            ) : (
              <XCircle className="w-8 h-8 text-[#E51E3A] shrink-0" />
            )}
            <h1 className={`text-4xl font-black tracking-tight ${
              isHealthy ? 'text-emerald-700' : isReview ? 'text-amber-700' : 'text-[#E51E3A]'
            }`}>
              {isHealthy ? t('healthy') : isReview ? 'REVIEW' : t('defective')}
            </h1>
          </div>
          {/* Secondary: internal grade code */}
          <p className="text-xs font-bold text-[#163A2D]/60 uppercase tracking-wide">
            {gradeName} · {explanation?.headline || 'Surface Quality Assessed'}
          </p>
        </div>

        {/* Confidence metric */}
        <div className="flex items-center justify-center gap-2">
          <div className="bg-white rounded-2xl px-6 py-3 shadow-2xs border border-[#163A2D]/10 text-center">
            <span className="text-[10px] font-bold text-[#163A2D]/60 uppercase block">Confidence</span>
            <span className="text-3xl font-black text-[#163A2D]">{confPercent}%</span>
          </div>
        </div>
      </div>

      {/* Inspection Metadata */}
      <div className="bg-white border border-[#163A2D]/15 rounded-3xl p-4 shadow-2xs space-y-2.5">
        <h3 className="text-[10px] font-black uppercase tracking-wider text-[#163A2D]/70">
          Inspection Details
        </h3>
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="flex items-start gap-2 bg-[#F7F1E7] p-2.5 rounded-xl border border-[#163A2D]/10">
            <Hash className="w-3.5 h-3.5 text-[#163A2D]/50 shrink-0 mt-0.5" />
            <div>
              <span className="text-[9px] font-bold text-[#163A2D]/60 block uppercase">Inspection ID</span>
              <span className="font-black text-[#163A2D] text-[10px] break-all">{inspection_id}</span>
            </div>
          </div>
          <div className="flex items-start gap-2 bg-[#F7F1E7] p-2.5 rounded-xl border border-[#163A2D]/10">
            <Hash className="w-3.5 h-3.5 text-[#163A2D]/50 shrink-0 mt-0.5" />
            <div>
              <span className="text-[9px] font-bold text-[#163A2D]/60 block uppercase">Batch ID</span>
              <span className="font-black text-[#163A2D] text-[10px]">{batch_id}</span>
            </div>
          </div>
          <div className="flex items-start gap-2 bg-[#F7F1E7] p-2.5 rounded-xl border border-[#163A2D]/10">
            <Clock className="w-3.5 h-3.5 text-[#163A2D]/50 shrink-0 mt-0.5" />
            <div>
              <span className="text-[9px] font-bold text-[#163A2D]/60 block uppercase">Model</span>
              <span className="font-black text-[#163A2D] text-[10px]">{result.model?.model_name || 'YOLO26n-cls'}</span>
            </div>
          </div>
          <div className="flex items-start gap-2 bg-[#F7F1E7] p-2.5 rounded-xl border border-[#163A2D]/10">
            <Cpu className="w-3.5 h-3.5 text-[#163A2D]/50 shrink-0 mt-0.5" />
            <div>
              <span className="text-[9px] font-bold text-[#163A2D]/60 block uppercase">Assessment</span>
              <span className="font-black text-[#163A2D] text-[10px]">Surface quality</span>
            </div>
          </div>
        </div>
      </div>

      {/* Surface Defect Indicators — only shown when binary classifier returned non-zero counts */}
      {hasAnyDefects && (
        <div className="bg-white border border-[#163A2D]/15 rounded-3xl p-4 shadow-2xs space-y-2.5">
          <h3 className="text-xs font-black uppercase tracking-wider text-[#163A2D]">
            {t('defectFlags')}
          </h3>
          <p className="text-[10px] text-[#163A2D]/60 font-medium">
            Surface characteristics flagged by the classification model.
          </p>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className={`p-2.5 rounded-xl border flex items-center justify-between ${stats!.damaged_count > 0 ? 'bg-rose-50 border-rose-200 text-[#E51E3A]' : 'bg-[#F7F1E7] border-[#163A2D]/10 text-[#163A2D]'}`}>
              <span className="font-bold">{t('damaged')}</span>
              <span className="font-black">{stats!.damaged_count > 0 ? 'YES' : 'NO'}</span>
            </div>
            <div className={`p-2.5 rounded-xl border flex items-center justify-between ${stats!.rotten_count > 0 ? 'bg-rose-50 border-rose-200 text-[#E51E3A]' : 'bg-[#F7F1E7] border-[#163A2D]/10 text-[#163A2D]'}`}>
              <span className="font-bold">{t('rotten')}</span>
              <span className="font-black">{stats!.rotten_count > 0 ? 'YES' : 'NO'}</span>
            </div>
            <div className={`p-2.5 rounded-xl border flex items-center justify-between ${stats!.sprouted_count > 0 ? 'bg-rose-50 border-rose-200 text-[#E51E3A]' : 'bg-[#F7F1E7] border-[#163A2D]/10 text-[#163A2D]'}`}>
              <span className="font-bold">{t('sprouted')}</span>
              <span className="font-black">{stats!.sprouted_count > 0 ? 'YES' : 'NO'}</span>
            </div>
            <div className={`p-2.5 rounded-xl border flex items-center justify-between ${stats!.undersized_count > 0 ? 'bg-amber-50 border-amber-200 text-amber-800' : 'bg-[#F7F1E7] border-[#163A2D]/10 text-[#163A2D]'}`}>
              <span className="font-bold">{t('undersized')}</span>
              <span className="font-black">{stats!.undersized_count > 0 ? 'YES' : 'NO'}</span>
            </div>
          </div>
        </div>
      )}

      {/* Scope Disclaimer */}
      <div className="p-3.5 bg-white border border-[#163A2D]/15 rounded-2xl flex items-start gap-2.5 shadow-2xs">
        <Info className="w-4 h-4 text-[#E51E3A] shrink-0 mt-0.5" />
        <div className="text-[11px] text-[#163A2D]/80 leading-tight space-y-1">
          <strong className="block">{t('externalDisclaimer')}</strong>
          <span className="block text-[#163A2D]/60 text-[10px]">{t('pilotBenchmark')}</span>
        </div>
      </div>

      {/* Bottom Actions */}
      <div className="space-y-2 pt-1">
        <div className="grid grid-cols-2 gap-2">
          <button
            onClick={() => onNavigate('evidence')}
            className="py-3.5 px-3 bg-[#163A2D] hover:bg-[#163A2D]/90 text-white border border-[#163A2D] rounded-2xl font-bold text-xs shadow-sm flex items-center justify-center gap-1.5 active:scale-95 transition-all cursor-pointer"
          >
            <Eye className="w-4 h-4" />
            <span>{t('viewEvidence')}</span>
          </button>

          <button
            onClick={() => onNavigate('report')}
            className="py-3.5 px-3 bg-white hover:bg-[#F7F1E7] text-[#163A2D] border border-[#163A2D]/20 rounded-2xl font-bold text-xs shadow-2xs flex items-center justify-center gap-1.5 active:scale-95 transition-all cursor-pointer"
          >
            <FileText className="w-4 h-4 text-[#163A2D]/70" />
            <span>{t('generateReport')}</span>
          </button>
        </div>

        <button
          onClick={onNewInspection}
          className="w-full py-3.5 bg-[#E51E3A] hover:bg-[#c91530] text-white rounded-2xl font-black text-xs uppercase tracking-wider shadow-md flex items-center justify-center gap-2 active:scale-95 transition-all cursor-pointer"
        >
          <RefreshCw className="w-4 h-4" />
          <span>{t('newInspection')}</span>
        </button>
      </div>
    </div>
  );
};
