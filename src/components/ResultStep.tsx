import React from 'react';
import {
  AlertTriangle,
  FileText,
  Eye,
  RefreshCw,
  ShieldAlert,
  HelpCircle,
} from 'lucide-react';
import { CanonicalInspectionResult, AppRoute } from '../types';

interface ResultStepProps {
  result: CanonicalInspectionResult;
  onNavigate: (route: AppRoute) => void;
  onNewInspection: () => void;
}

export const ResultStep: React.FC<ResultStepProps> = ({
  result,
  onNavigate,
  onNewInspection,
}) => {
  const {
    status,
    grading,
    batch_statistics: stats,
    explanation,
    confidence,
    review,
    model,
  } = result;

  const isDevelopmentMock = model?.source === 'development_mock';

  // 1. RETAKE REQUIRED STATE
  if (status === 'RETAKE_REQUIRED' || result.image_quality?.quality_status === 'RETAKE_REQUIRED') {
    return (
      <div className="max-w-xl mx-auto px-4 py-8 space-y-6">
        <div className="bg-amber-50 border-2 border-amber-400 rounded-3xl p-6 shadow-md text-center space-y-4">
          <div className="w-14 h-14 bg-amber-100 text-amber-700 rounded-full flex items-center justify-center mx-auto">
            <AlertTriangle className="w-8 h-8" />
          </div>
          <div className="space-y-1">
            <h2 className="text-xl font-bold text-amber-900">IMAGE QUALITY INSUFFICIENT</h2>
            <p className="text-xs text-amber-800 font-medium">Quality Gate Screening Flagged Retake</p>
          </div>

          <div className="bg-white border border-amber-200 rounded-2xl p-4 text-left space-y-2 text-xs text-stone-700">
            <div className="font-semibold text-amber-900">Quality Check Recommendations:</div>
            <ul className="list-disc pl-4 space-y-1">
              {explanation.limitations.map((lim, idx) => (
                <li key={idx}>{lim}</li>
              ))}
            </ul>
          </div>

          <button
            onClick={onNewInspection}
            className="w-full py-3.5 px-4 bg-amber-600 text-white rounded-2xl font-bold shadow-md hover:bg-amber-700 transition-all flex items-center justify-center gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            <span>RETAKE IMAGE</span>
          </button>
        </div>
      </div>
    );
  }

  // 2. MODEL UNAVAILABLE STATE
  if (status === 'MODEL_UNAVAILABLE') {
    return (
      <div className="max-w-xl mx-auto px-4 py-8 space-y-6">
        <div className="bg-red-50 border-2 border-red-400 rounded-3xl p-6 shadow-md text-center space-y-4">
          <div className="w-14 h-14 bg-red-100 text-red-700 rounded-full flex items-center justify-center mx-auto">
            <ShieldAlert className="w-8 h-8" />
          </div>
          <div className="space-y-1">
            <h2 className="text-xl font-bold text-red-900">AI MODEL UNAVAILABLE</h2>
            <p className="text-xs text-red-800">Production AI model is currently offline/uninitialized.</p>
          </div>

          <button
            onClick={onNewInspection}
            className="w-full py-3.5 px-4 bg-red-700 text-white rounded-2xl font-bold shadow-md hover:bg-red-800 transition-all flex items-center justify-center gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            <span>TRY AGAIN</span>
          </button>
        </div>
      </div>
    );
  }

  // 3. SUCCESS / REVIEW REQUIRED RESULT VIEW
  return (
    <div className="max-w-xl mx-auto px-4 py-6 space-y-6">
      {/* Top Header & Model Source Disclosure */}
      <div className="flex items-center justify-between">
        <div>
          <span className="text-xs uppercase tracking-wider text-stone-500 font-semibold">Inspection Result</span>
          <h1 className="text-lg font-bold text-[#0F281E]">Batch {result.batch_id}</h1>
        </div>
        {isDevelopmentMock && (
          <span className="px-2.5 py-1 bg-amber-100 border border-amber-300 text-amber-900 rounded-full text-[11px] font-semibold">
            Development inference — not production AI
          </span>
        )}
      </div>

      {/* Review Required Alert (If applicable) */}
      {review?.review_status === 'REVIEW_REQUIRED' && (
        <div className="bg-amber-50 border-2 border-amber-400 rounded-2xl p-4 text-xs text-amber-900 space-y-1">
          <div className="font-bold flex items-center gap-1.5 text-amber-800">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <span>HUMAN REVIEW REQUIRED</span>
          </div>
          <p>Reason: {review.review_reason || 'Inspection confidence below threshold'}</p>
        </div>
      )}

      {/* Main Grade & Quality Score Cards */}
      <div className="grid grid-cols-2 gap-4">
        {/* Grade Card */}
        <div className="bg-[#0F281E] text-white rounded-3xl p-5 shadow-lg flex flex-col justify-between">
          <span className="text-[11px] font-semibold text-emerald-300 uppercase tracking-wider">
            Prototype Grade
          </span>
          <div className="my-2">
            <div className="text-3xl font-black text-white tracking-tight">
              {grading?.prototype_grade || 'Grade-C'}
            </div>
            <span className="inline-block mt-1 px-2 py-0.5 bg-[#2D5A27] text-[10px] font-bold uppercase rounded text-emerald-200">
              {result.sampling_status}
            </span>
          </div>
          <div className="text-[10px] text-stone-300">
            Confidence: {(confidence * 100).toFixed(0)}%
          </div>
        </div>

        {/* Commercial Quality Score Card */}
        <div className="bg-white border border-stone-200 rounded-3xl p-5 shadow-sm flex flex-col justify-between">
          <span className="text-[11px] font-semibold text-stone-500 uppercase tracking-wider">
            Quality Score
          </span>
          <div className="my-2">
            <div className="text-3xl font-black text-[#0F281E]">
              {grading?.quality_score !== undefined ? `${grading.quality_score.toFixed(0)} / 100` : 'N/A'}
            </div>
            <div className="text-[11px] text-stone-500 mt-0.5">
              Grade A: <strong>{grading?.grade_a_percent.toFixed(1)}%</strong>
            </div>
          </div>
          <div className="text-[10px] text-stone-400">
            Profile: {grading?.grading_profile_id || 'prototype-procurement-v1'}
          </div>
        </div>
      </div>

      {/* Lot Summary Quick Bar */}
      <div className="bg-white border border-stone-200 rounded-2xl p-4 grid grid-cols-3 gap-2 text-center text-xs">
        <div>
          <div className="text-stone-400 text-[10px] uppercase font-semibold">Grade-A</div>
          <div className="font-bold text-emerald-700 text-sm">{stats.healthy_percentage.toFixed(1)}%</div>
        </div>
        <div>
          <div className="text-stone-400 text-[10px] uppercase font-semibold">URS Portion</div>
          <div className="font-bold text-amber-700 text-sm">{stats.undersized_percentage.toFixed(1)}%</div>
        </div>
        <div>
          <div className="text-stone-400 text-[10px] uppercase font-semibold">Analyzed Bulbs</div>
          <div className="font-bold text-[#0F281E] text-sm">{stats.total_analyzed_onions}</div>
        </div>
      </div>

      {/* Defect Breakdown List */}
      <div className="bg-white border border-stone-200 rounded-3xl p-5 shadow-sm space-y-3">
        <h3 className="text-xs font-bold uppercase tracking-wider text-stone-600">
          Sample Lot Defect Breakdown
        </h3>
        <div className="space-y-2 text-xs">
          <div className="flex justify-between items-center py-1.5 border-b border-stone-100">
            <span className="font-medium text-emerald-800">Healthy (Grade-A)</span>
            <span className="font-bold">{stats.healthy_count} ({stats.healthy_percentage.toFixed(1)}%)</span>
          </div>
          <div className="flex justify-between items-center py-1.5 border-b border-stone-100">
            <span className="font-medium text-stone-700">Mechanical Damage</span>
            <span className="font-bold">{stats.damaged_count} ({stats.damaged_percentage.toFixed(1)}%)</span>
          </div>
          <div className="flex justify-between items-center py-1.5 border-b border-stone-100">
            <span className="font-medium text-red-700">Rot / Decay</span>
            <span className="font-bold">{stats.rotten_count} ({stats.rotten_percentage.toFixed(1)}%)</span>
          </div>
          <div className="flex justify-between items-center py-1.5 border-b border-stone-100">
            <span className="font-medium text-amber-700">Neck Sprouting</span>
            <span className="font-bold">{stats.sprouted_count} ({stats.sprouted_percentage.toFixed(1)}%)</span>
          </div>
          <div className="flex justify-between items-center py-1.5">
            <span className="font-medium text-amber-800">Under-Sized (&lt; 45mm)</span>
            <span className="font-bold">{stats.undersized_count} ({stats.undersized_percentage.toFixed(1)}%)</span>
          </div>
        </div>
      </div>

      {/* Why This Grade (Explanation Engine Output) */}
      <div className="bg-stone-50 border border-stone-200 rounded-3xl p-5 space-y-3">
        <div className="flex items-center gap-1.5 text-[#0F281E] font-bold text-xs uppercase tracking-wider">
          <HelpCircle className="w-4 h-4 text-[#2D5A27]" />
          <span>Why This Result?</span>
        </div>
        <div className="text-sm font-semibold text-stone-800">{explanation.headline}</div>
        
        <div className="space-y-1.5 text-xs text-stone-700">
          <div className="font-semibold text-stone-900">Primary Factors:</div>
          <ul className="list-disc pl-4 space-y-1">
            {explanation.primary_factors.map((f, i) => (
              <li key={i}>{f}</li>
            ))}
          </ul>
        </div>

        {explanation.limitations && (
          <div className="space-y-1.5 text-[11px] text-stone-500 pt-2 border-t border-stone-200">
            <div className="font-semibold text-stone-700">Mandatory Limitations:</div>
            <ul className="list-disc pl-4 space-y-0.5">
              {explanation.limitations.map((lim, i) => (
                <li key={i}>{lim}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="grid grid-cols-2 gap-3 pt-2">
        <button
          onClick={() => onNavigate('evidence')}
          className="py-3.5 px-4 bg-[#2D5A27] text-white rounded-2xl font-bold shadow-md hover:bg-[#23471F] transition-all flex items-center justify-center gap-2 text-xs"
        >
          <Eye className="w-4 h-4" />
          <span>VIEW EVIDENCE</span>
        </button>
        <button
          onClick={() => onNavigate('report')}
          className="py-3.5 px-4 bg-white text-[#0F281E] border border-stone-300 rounded-2xl font-bold hover:bg-stone-50 transition-all flex items-center justify-center gap-2 text-xs"
        >
          <FileText className="w-4 h-4 text-stone-600" />
          <span>DIGITAL REPORT</span>
        </button>
      </div>

      <button
        onClick={onNewInspection}
        className="w-full py-3 bg-stone-100 text-stone-700 border border-stone-200 rounded-2xl font-semibold text-xs hover:bg-stone-200 transition-all"
      >
        START NEW INSPECTION
      </button>
    </div>
  );
};
