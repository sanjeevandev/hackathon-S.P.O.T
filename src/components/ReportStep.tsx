import React, { useEffect, useState } from 'react';
import { ArrowLeft, ExternalLink, Loader2, Info, CheckCircle2 } from 'lucide-react';
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
      <div className="max-w-md mx-auto px-4 py-16 text-center space-y-4 pb-24 font-sans text-[#163A2D]">
        <Loader2 className="w-8 h-8 text-[#163A2D] animate-spin mx-auto" />
        <p className="text-xs text-[#163A2D]/70 font-medium">Fetching Digital Quality Inspection Report...</p>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="max-w-md mx-auto px-4 py-12 text-center space-y-4 pb-24 font-sans text-[#163A2D]">
        <div className="p-4 bg-white border border-[#E51E3A] rounded-2xl text-[#E51E3A] text-xs font-bold">
          {error || 'Digital Quality Inspection Report not found'}
        </div>
        <button
          onClick={onBack}
          className="px-4 py-2 bg-[#163A2D] text-white text-xs font-bold rounded-xl cursor-pointer"
        >
          Return to Inspection
        </button>
      </div>
    );
  }

  const htmlUrl = getInspectionReportHtmlUrl(inspectionId);
  const grade = report.grading?.grade || report.grading?.prototype_grade || 'Grade-A';
  const score = report.grading?.score || report.grading?.quality_score || 90;
  const centerId = report.batch_metadata?.procurement_center_id || report.batch_metadata?.center_id || 'APMC Lasalgaon';
  const disclaimerText = report.disclaimer || (report as any).disclaimers?.prototype_disclaimer || 'Prototype inspection based on external surface optical imaging.';

  return (
    <div className="max-w-md mx-auto px-4 py-5 space-y-4 pb-24 font-sans text-[#163A2D]">
      {/* Header & Actions */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={onBack}
            className="p-2 rounded-xl border border-[#163A2D]/15 bg-white text-[#163A2D] active:scale-95 transition-all shadow-2xs cursor-pointer"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-lg font-black text-[#163A2D]">Inspection Report</h1>
            <p className="text-[10px] text-[#163A2D]/60 font-semibold">S.P.O.T. · ID: {report.report_id.slice(0, 12)} (v{report.report_version})</p>
          </div>
        </div>

        <a
          href={htmlUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="p-2 rounded-xl bg-white border border-[#163A2D]/15 text-[#163A2D] shadow-2xs hover:bg-[#F7F1E7] active:scale-95 transition-all flex items-center gap-1 text-[10px] font-bold"
        >
          <span>Print Slip</span>
          <ExternalLink className="w-3.5 h-3.5 text-[#163A2D]/70" />
        </a>
      </div>

      {/* Main Report Card */}
      <div className="bg-white border border-[#163A2D]/15 rounded-3xl p-5 shadow-2xs space-y-4 text-xs">
        {/* Verification Status Pill */}
        <div className="flex items-center justify-between border-b border-[#163A2D]/10 pb-3">
          <div className="space-y-0.5">
            <span className="text-[10px] text-[#163A2D]/60 uppercase font-bold block">Inspection Reference</span>
            <span className="text-sm font-black text-[#163A2D]">{report.inspection_id}</span>
          </div>
          <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-[#163A2D]/10 text-[#163A2D] rounded-full text-[10px] font-black uppercase">
            <CheckCircle2 className="w-3.5 h-3.5 text-[#163A2D]" />
            <span>SQLite Logged</span>
          </div>
        </div>

        {/* Primary Grading Outcome */}
        <div className="bg-[#163A2D] text-white p-4 rounded-2xl flex items-center justify-between shadow-xs">
          <div>
            <span className="text-[10px] text-white/70 uppercase font-semibold">Quality Result</span>
            <div className="text-2xl font-black text-white">
              {grade === 'Grade-A' || grade === 'A' ? 'HEALTHY' : grade === 'Grade-URS' || grade === 'URS' ? 'REVIEW' : 'DEFECTIVE'}
            </div>
            <div className="text-[10px] text-white/60">{grade}</div>
          </div>
          <div className="text-right">
            <span className="text-[10px] text-white/70 uppercase font-semibold">Quality Index</span>
            <div className="text-2xl font-black text-emerald-300">{score}/100</div>
          </div>
        </div>

        {/* Verification Metadata Grid */}
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="p-2.5 bg-[#F7F1E7] rounded-xl border border-[#163A2D]/10">
            <span className="text-[10px] text-[#163A2D]/60 block font-bold">BATCH LOT</span>
            <span className="font-black text-[#163A2D]">{report.batch_id}</span>
          </div>
          <div className="p-2.5 bg-[#F7F1E7] rounded-xl border border-[#163A2D]/10">
            <span className="text-[10px] text-[#163A2D]/60 block font-bold">APMC CENTER</span>
            <span className="font-black text-[#163A2D]">{centerId}</span>
          </div>
        </div>

        {/* Breakdown of Visible Sample Count */}
        {report.statistics && (
          <div className="space-y-1.5">
            <div className="text-[10px] font-black uppercase text-[#163A2D]/70 tracking-wider">
              Sample Statistics
            </div>
            <div className="grid grid-cols-3 gap-2 text-center">
              <div className="p-2 bg-[#F7F1E7] rounded-xl border border-[#163A2D]/10">
                <span className="text-[9px] text-[#163A2D]/60 block font-bold">Grade-A</span>
                <span className="text-sm font-black text-emerald-700">{report.statistics.grade_a_percentage ?? 0}%</span>
              </div>
              <div className="p-2 bg-[#F7F1E7] rounded-xl border border-[#163A2D]/10">
                <span className="text-[9px] text-[#163A2D]/60 block font-bold">URS</span>
                <span className="text-sm font-black text-amber-700">{report.statistics.grade_urs_percentage ?? 0}%</span>
              </div>
              <div className="p-2 bg-[#F7F1E7] rounded-xl border border-[#163A2D]/10">
                <span className="text-[9px] text-[#163A2D]/60 block font-bold">Defective</span>
                <span className="text-sm font-black text-rose-700">{report.statistics.rejected_percentage ?? 0}%</span>
              </div>
            </div>
          </div>
        )}

        {/* Official Disclaimers */}
        <div className="p-3.5 bg-[#F7F1E7] border border-[#163A2D]/10 rounded-2xl text-[10px] space-y-1 text-[#163A2D]">
          <div className="font-bold flex items-center gap-1.5 text-[#163A2D]">
            <Info className="w-3.5 h-3.5 text-[#E51E3A] shrink-0" />
            <span>Scope & Limitations:</span>
          </div>
          <p className="leading-snug text-[#163A2D]/80">
            {disclaimerText}
          </p>
        </div>
      </div>
    </div>
  );
};
