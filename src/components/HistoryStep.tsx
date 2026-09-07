import React, { useEffect, useState } from 'react';
import { ArrowLeft, History, ChevronRight, Loader2 } from 'lucide-react';
import { getInspectionHistory } from '../api/inspections';
import { HistoryItem } from '../types';

interface HistoryStepProps {
  onSelectInspection: (inspectionId: string) => void;
  onBack: () => void;
}

export const HistoryStep: React.FC<HistoryStepProps> = ({
  onSelectInspection,
  onBack,
}) => {
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadHistory() {
      setLoading(true);
      setError(null);
      try {
        const data = await getInspectionHistory();
        setHistory(data);
      } catch (err: any) {
        setError(err.message || 'Failed to retrieve inspection history');
      } finally {
        setLoading(false);
      }
    }
    loadHistory();
  }, []);

  return (
    <div className="max-w-2xl mx-auto px-4 py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <button
          onClick={onBack}
          className="p-2 rounded-xl border border-stone-200 hover:bg-stone-100 text-stone-700"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div>
          <h1 className="text-xl font-bold text-[#0F281E]">Inspection History</h1>
          <p className="text-xs text-stone-500">Persisted inspection records & reports</p>
        </div>
      </div>

      {loading ? (
        <div className="py-16 text-center space-y-3">
          <Loader2 className="w-8 h-8 text-[#2D5A27] animate-spin mx-auto" />
          <p className="text-xs text-stone-500 font-medium">Loading historical records...</p>
        </div>
      ) : error ? (
        <div className="p-4 bg-red-50 border border-red-200 rounded-2xl text-red-800 text-xs font-semibold text-center">
          {error}
        </div>
      ) : history.length === 0 ? (
        <div className="bg-stone-50 border border-stone-200 rounded-3xl p-8 text-center space-y-3">
          <History className="w-10 h-10 text-stone-400 mx-auto" />
          <div className="text-sm font-bold text-stone-700">No Past Inspections Found</div>
          <p className="text-xs text-stone-500">Completed inspections will automatically persist here.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {history.map((item) => {
            const gr = item.grading_result;
            return (
              <button
                key={item.inspection_id}
                onClick={() => onSelectInspection(item.inspection_id)}
                className="w-full bg-white border border-stone-200 rounded-2xl p-4 shadow-sm hover:border-stone-300 transition-all text-left flex items-center justify-between group"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-sm text-[#0F281E]">
                      {item.batch_id}
                    </span>
                    <span className="px-2 py-0.5 bg-stone-100 border border-stone-200 text-[10px] font-semibold text-stone-600 rounded">
                      {item.inspection_id}
                    </span>
                  </div>

                  <div className="flex items-center gap-3 text-xs text-stone-500">
                    <span>{new Date(item.started_at).toLocaleString()}</span>
                    <span>•</span>
                    <span className="font-semibold text-emerald-800">
                      Score: {gr?.quality_score !== undefined ? `${gr.quality_score.toFixed(0)}/100` : 'N/A'}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <div className="text-right">
                    <div className="text-base font-black text-[#2D5A27]">
                      {gr?.grade || 'Grade-C'}
                    </div>
                    <span className="text-[10px] font-semibold uppercase text-stone-400">
                      {gr?.sampling_status || 'SAMPLE_ONLY'}
                    </span>
                  </div>
                  <ChevronRight className="w-5 h-5 text-stone-400 group-hover:translate-x-1 transition-transform" />
                </div>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
};
