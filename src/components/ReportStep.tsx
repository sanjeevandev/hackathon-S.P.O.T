import React, { useEffect, useState } from 'react';
import { ArrowLeft, ShieldAlert, ExternalLink, Loader2 } from 'lucide-react';
import { getInspectionReport, getInspectionReportHtmlUrl } from '../api/reports';
import { InspectionReport } from '../types';

interface ReportStepProps {
  inspectionId: string;
  onBack: () => void;
}

export const ReportStep: React.FC<ReportStepProps> = ({
  inspectionId,
  onBack,
}) => {
  const [report, setReport] = useState<InspectionReport | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadReport() {
      setLoading(true);
      setError(null);
      try {
        const data = await getInspectionReport(inspectionId);
        setReport(data);
      } catch (err: any) {
        setError(err.message || 'Failed to load Digital Quality Inspection Report');
      } finally {
        setLoading(false);
      }
    }
    loadReport();
  }, [inspectionId]);

  if (loading) {
    return (
      <div className="max-w-xl mx-auto px-4 py-16 text-center space-y-4">
        <Loader2 className="w-8 h-8 text-[#2D5A27] animate-spin mx-auto" />
        <p className="text-xs text-stone-500 font-medium">Fetching Digital Quality Inspection Report...</p>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="max-w-xl mx-auto px-4 py-12 text-center space-y-4">
        <div className="p-4 bg-red-50 border border-red-200 rounded-2xl text-red-800 text-xs font-semibold">
          {error || 'Digital Quality Inspection Report not found'}
        </div>
        <button
          onClick={onBack}
          className="px-4 py-2 bg-stone-200 text-stone-800 text-xs font-bold rounded-xl"
        >
          Return to Inspection
        </button>
      </div>
    );
  }

  const htmlUrl = getInspectionReportHtmlUrl(inspectionId);

  return (
    <div className="max-w-2xl mx-auto px-4 py-6 space-y-6">
      {/* Header & Actions */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={onBack}
            className="p-2 rounded-xl border border-stone-200 hover:bg-stone-100 text-stone-700"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-xl font-bold text-[#0F281E]">Digital Quality Inspection Report</h1>
            <p className="text-xs text-stone-500">Report ID: {report.report_id} (v{report.report_version})</p>
          </div>
        </div>

        <a
          href={htmlUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="px-3 py-2 bg-[#2D5A27] text-white rounded-xl text-xs font-bold shadow hover:bg-[#23471F] flex items-center gap-1.5"
        >
          <ExternalLink className="w-3.5 h-3.5" />
          <span>HTML View</span>
        </a>
      </div>

      {/* Mandatory Disclaimer Banner */}
      <div className="bg-red-50 border border-red-300 rounded-2xl p-4 text-xs font-medium text-red-900 space-y-1">
        <div className="font-bold flex items-center gap-1.5 text-red-800">
          <ShieldAlert className="w-4 h-4 shrink-0" />
          <span>Statutory Prototype Disclaimer</span>
        </div>
        <p>{report.disclaimer}</p>
      </div>

      {/* Structured Document Content */}
      <div className="bg-white border border-stone-200 rounded-3xl p-6 shadow-sm space-y-6">
        {/* Metadata Summary */}
        <div className="grid grid-cols-2 gap-4 pb-4 border-b border-stone-100 text-xs">
          <div>
            <span className="text-[10px] uppercase font-bold text-stone-400">Batch Identifier</span>
            <div className="font-bold text-[#0F281E] text-sm">{report.batch_id}</div>
          </div>
          <div>
            <span className="text-[10px] uppercase font-bold text-stone-400">Generation Timestamp</span>
            <div className="font-semibold text-stone-700">{new Date(report.generated_at).toLocaleString()}</div>
          </div>
        </div>

        {/* Grade Summary Box */}
        <div className="bg-[#0F281E] text-white rounded-2xl p-5 flex items-center justify-between">
          <div>
            <span className="text-[10px] uppercase font-bold text-emerald-300 tracking-wider">Evaluated Prototype Grade</span>
            <div className="text-3xl font-black">{report.grading?.prototype_grade || 'Grade-C'}</div>
          </div>
          <div className="text-right">
            <span className="text-[10px] uppercase font-bold text-stone-400">Quality Score</span>
            <div className="text-2xl font-bold text-emerald-300">
              {report.grading?.quality_score !== undefined ? `${report.grading.quality_score.toFixed(1)} / 100` : 'N/A'}
            </div>
          </div>
        </div>

        {/* Lot Statistics */}
        <div className="space-y-2 text-xs">
          <h3 className="font-bold uppercase text-stone-600 text-[11px] tracking-wider">Sample Lot Statistics</h3>
          <div className="bg-stone-50 border border-stone-200 rounded-2xl p-4 space-y-2">
            <div className="flex justify-between border-b border-stone-200/60 pb-1.5 font-medium">
              <span>Total Analyzed Bulbs</span>
              <span className="font-bold">{report.statistics.total_analyzed_onions || 0}</span>
            </div>
            <div className="flex justify-between text-emerald-800">
              <span>Grade-A (Healthy)</span>
              <span className="font-bold">{(report.statistics.healthy_percentage || 0).toFixed(1)}% ({report.statistics.healthy_count || 0})</span>
            </div>
            <div className="flex justify-between text-stone-700">
              <span>Damaged</span>
              <span className="font-bold">{(report.statistics.damaged_percentage || 0).toFixed(1)}% ({report.statistics.damaged_count || 0})</span>
            </div>
            <div className="flex justify-between text-red-700">
              <span>Rot / Decay</span>
              <span className="font-bold">{(report.statistics.rotten_percentage || 0).toFixed(1)}% ({report.statistics.rotten_count || 0})</span>
            </div>
            <div className="flex justify-between text-amber-700">
              <span>Sprouted</span>
              <span className="font-bold">{(report.statistics.sprouted_percentage || 0).toFixed(1)}% ({report.statistics.sprouted_count || 0})</span>
            </div>
            <div className="flex justify-between text-amber-800">
              <span>Under-Sized (&lt; 45mm)</span>
              <span className="font-bold">{(report.statistics.undersized_percentage || 0).toFixed(1)}% ({report.statistics.undersized_count || 0})</span>
            </div>
          </div>
        </div>

        {/* Explanation Rationale */}
        <div className="space-y-2 text-xs">
          <h3 className="font-bold uppercase text-stone-600 text-[11px] tracking-wider">Assessment Rationale</h3>
          <div className="bg-stone-50 border border-stone-200 rounded-2xl p-4 space-y-2">
            <div className="font-semibold text-stone-900">{report.explanation.headline}</div>
            <ul className="list-disc pl-4 space-y-1 text-stone-700">
              {report.explanation.primary_factors?.map((f: string, i: number) => (
                <li key={i}>{f}</li>
              ))}
            </ul>
          </div>
        </div>

        {/* Limitations & Technical Context */}
        <div className="space-y-2 text-[11px] text-stone-500 pt-2 border-t border-stone-100">
          <div className="font-semibold text-stone-700">Mandatory Limitations:</div>
          <ul className="list-disc pl-4 space-y-0.5">
            {report.limitations.map((lim, i) => (
              <li key={i}>{lim}</li>
            ))}
          </ul>
        </div>

        {/* Traceability Footer */}
        <div className="bg-stone-100 border border-stone-200 rounded-2xl p-3.5 text-[10px] text-stone-600 space-y-1">
          <div>Vision Model: <strong>{report.model_information.model_name} ({report.model_information.model_version}) [{report.model_information.source}]</strong></div>
          <div>Grading Profile: <strong>{report.grading_profile_information.profile_name} ({report.grading_profile_information.version})</strong></div>
        </div>
      </div>
    </div>
  );
};
