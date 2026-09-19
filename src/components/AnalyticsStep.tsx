import React, { useState, useEffect } from 'react';
import { ArrowLeft, CheckCircle, XCircle, Loader2 } from 'lucide-react';
import { getInspectionHistory } from '../api/inspections';
import { HistoryItem } from '../types';

interface AnalyticsStepProps {
  onBack: () => void;
  onStartNewInspection: () => void;
}

export const AnalyticsStep: React.FC<AnalyticsStepProps> = ({
  onBack,
  onStartNewInspection,
}) => {
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [timeFilter, setTimeFilter] = useState<'today' | 'week' | 'month'>('week');

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      try {
        const data = await getInspectionHistory();
        setHistory(data);
      } catch (err) {
        console.error('Failed to load history for analytics', err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  // Filter history by timeframe
  const now = new Date().getTime();
  const filteredHistory = history.filter((item) => {
    const itemTime = new Date(item.started_at).getTime();
    if (isNaN(itemTime)) return true;
    const diffHours = (now - itemTime) / (1000 * 60 * 60);
    if (timeFilter === 'today') return diffHours <= 24;
    if (timeFilter === 'week') return diffHours <= 168;
    return diffHours <= 720;
  });

  const totalCount = filteredHistory.length;
  let healthyCount = 0;
  let defectiveCount = 0;
  let reviewCount = 0;
  let totalScoreSum = 0;
  let scoreCount = 0;

  filteredHistory.forEach((item) => {
    const grade = item.grading_result?.grade;
    if (grade === 'Grade-A' || grade === 'A') {
      healthyCount += 1;
    } else if (grade === 'Grade-C' || grade === 'C' || grade === 'REJECTED') {
      defectiveCount += 1;
    } else {
      reviewCount += 1;
    }

    if (item.grading_result?.quality_score !== undefined) {
      totalScoreSum += item.grading_result.quality_score;
      scoreCount += 1;
    }
  });

  const healthyPct = totalCount > 0 ? (healthyCount / totalCount) * 100 : 0;
  const defectivePct = totalCount > 0 ? (defectiveCount / totalCount) * 100 : 0;
  const reviewPct = totalCount > 0 ? (reviewCount / totalCount) * 100 : 0;
  const avgScore = scoreCount > 0 ? totalScoreSum / scoreCount : 0;

  return (
    <div className="max-w-md mx-auto px-4 py-6 space-y-6 pb-24 font-sans text-[#163A2D]">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={onBack}
            className="p-2 rounded-xl border border-[#163A2D]/15 bg-white text-[#163A2D] active:scale-95 shadow-2xs"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-xl font-black text-[#163A2D]">Quality Analytics</h1>
            <p className="text-xs text-[#163A2D]/70">Regional lot quality aggregation</p>
          </div>
        </div>
      </div>

      {/* Time Horizon Filter Chips */}
      <div className="flex items-center gap-2 p-1 bg-white rounded-2xl border border-[#163A2D]/15 shadow-2xs">
        {(['today', 'week', 'month'] as const).map((filter) => (
          <button
            key={filter}
            onClick={() => setTimeFilter(filter)}
            className={`flex-1 py-2 rounded-xl text-xs font-bold capitalize transition-all ${
              timeFilter === filter
                ? 'bg-[#163A2D] text-white shadow-2xs'
                : 'text-[#163A2D]/70 hover:text-[#163A2D]'
            }`}
          >
            {filter}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="py-16 text-center space-y-3">
          <Loader2 className="w-8 h-8 text-[#163A2D] animate-spin mx-auto" />
          <p className="text-xs text-[#163A2D]/70 font-medium">Aggregating quality records...</p>
        </div>
      ) : totalCount === 0 ? (
        <div className="bg-white border border-[#163A2D]/15 rounded-3xl p-8 text-center space-y-3 shadow-2xs">
          <div className="text-sm font-black text-[#163A2D]">No Inspections for this Timeframe</div>
          <p className="text-xs text-[#163A2D]/70">
            Completed scans will aggregate into quality analytics.
          </p>
          <div className="pt-2">
            <button
              onClick={onStartNewInspection}
              className="px-5 py-2.5 bg-[#E51E3A] hover:bg-[#c91530] text-white text-xs font-black rounded-xl shadow-xs uppercase tracking-wide"
            >
              START FIRST SCAN
            </button>
          </div>
        </div>
      ) : (
        <>
          {/* Main Quality Score Card */}
          <div className="bg-[#163A2D] text-white rounded-3xl p-6 shadow-md border border-[#163A2D] space-y-3">
            <span className="text-[10px] uppercase font-bold text-white/80 tracking-wider">
              Mean Quality Score ({timeFilter})
            </span>
            <div className="flex items-baseline gap-2">
              <span className="text-4xl font-black">{avgScore.toFixed(0)}</span>
              <span className="text-lg font-bold text-white/75">/ 100</span>
            </div>
            <p className="text-xs text-white/75">
              Based on {totalCount} verified optical lot scans.
            </p>
          </div>

          {/* Ratio Breakdown Cards */}
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-white border border-[#163A2D]/15 rounded-2xl p-4 shadow-2xs space-y-1">
              <div className="flex items-center gap-1.5 text-xs font-bold text-[#163A2D]">
                <CheckCircle className="w-4 h-4 text-[#163A2D]" />
                <span>Healthy Lots</span>
              </div>
              <div className="text-2xl font-black text-[#163A2D]">
                {healthyPct.toFixed(1)}%
              </div>
              <span className="text-[10px] text-[#163A2D]/60 font-semibold">{healthyCount} lots passed</span>
            </div>

            <div className="bg-white border border-[#163A2D]/15 rounded-2xl p-4 shadow-2xs space-y-1">
              <div className="flex items-center gap-1.5 text-xs font-bold text-[#E51E3A]">
                <XCircle className="w-4 h-4 text-[#E51E3A]" />
                <span>Defective Lots</span>
              </div>
              <div className="text-2xl font-black text-[#E51E3A]">
                {defectivePct.toFixed(1)}%
              </div>
              <span className="text-[10px] text-[#E51E3A]/80 font-semibold">{defectiveCount} lots flagged</span>
            </div>
          </div>

          {/* Distribution Bar */}
          <div className="bg-white border border-[#163A2D]/15 rounded-3xl p-5 shadow-2xs space-y-3">
            <h3 className="text-xs font-black uppercase tracking-wider text-[#163A2D]">
              Quality Classification Ratio
            </h3>
            <div className="w-full h-4 bg-[#F7F1E7] rounded-full overflow-hidden flex">
              <div style={{ width: `${healthyPct}%` }} className="bg-[#163A2D] h-full" title={`Healthy: ${healthyPct.toFixed(1)}%`} />
              <div style={{ width: `${reviewPct}%` }} className="bg-[#F7F1E7] border border-[#163A2D]/20 h-full" title={`Review: ${reviewPct.toFixed(1)}%`} />
              <div style={{ width: `${defectivePct}%` }} className="bg-[#E51E3A] h-full" title={`Defective: ${defectivePct.toFixed(1)}%`} />
            </div>
            <div className="flex justify-between text-[10px] font-bold text-[#163A2D]/70 pt-1">
              <span>Healthy: {healthyPct.toFixed(0)}%</span>
              <span>Needs Review: {reviewPct.toFixed(0)}%</span>
              <span className="text-[#E51E3A]">Defective: {defectivePct.toFixed(0)}%</span>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
