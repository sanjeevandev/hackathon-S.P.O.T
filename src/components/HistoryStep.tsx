import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { ArrowLeft, History, ChevronRight, Loader2, Search, CheckCircle2, XCircle, AlertTriangle } from 'lucide-react';
import { getInspectionHistory } from '../api/inspections';
import { HistoryItem } from '../types';

/** Maps internal grade codes to user-facing HEALTHY / DEFECTIVE / REVIEW */
function gradeToLabel(grade?: string): 'HEALTHY' | 'DEFECTIVE' | 'REVIEW' | null {
  if (!grade) return null;
  if (grade === 'Grade-A' || grade === 'A') return 'HEALTHY';
  if (grade === 'Grade-URS' || grade === 'URS') return 'REVIEW';
  if (grade === 'Grade-C' || grade === 'C' || grade === 'REJECTED') return 'DEFECTIVE';
  return null;
}

interface HistoryStepProps {
  onSelectInspection: (inspectionId: string) => void;
  onBack: () => void;
}

export const HistoryStep: React.FC<HistoryStepProps> = ({
  onSelectInspection,
  onBack,
}) => {
  const { t } = useTranslation();
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [filterType, setFilterType] = useState<'ALL' | 'HEALTHY' | 'DEFECTIVE' | 'REVIEW'>('ALL');

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

  const filteredItems = history.filter((item) => {
    const matchesSearch =
      item.batch_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.inspection_id.toLowerCase().includes(searchQuery.toLowerCase());

    if (!matchesSearch) return false;

    const grade = item.grading_result?.grade;
    if (filterType === 'HEALTHY') return grade === 'Grade-A' || grade === 'A';
    if (filterType === 'DEFECTIVE') return grade === 'Grade-C' || grade === 'C' || grade === 'REJECTED';
    if (filterType === 'REVIEW') return item.review_status === 'REVIEW_REQUIRED' || grade === 'Grade-URS';
    return true;
  });

  return (
    <div className="max-w-md mx-auto px-4 py-5 space-y-4 pb-24 font-sans text-[#163A2D]">
      {/* Header */}
      <div className="flex items-center gap-3">
        <button
          onClick={onBack}
          className="p-2 rounded-xl border border-[#163A2D]/15 bg-white text-[#163A2D] active:scale-95 transition-all shadow-2xs cursor-pointer"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div>
          <h1 className="text-xl font-black text-[#163A2D]">{t('history')}</h1>
          <p className="text-xs text-[#163A2D]/70">Persisted inspection records & audit trail</p>
        </div>
      </div>

      {/* Search Input Field */}
      <div className="relative">
        <Search className="w-4 h-4 text-[#163A2D]/50 absolute left-3.5 top-3.5" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder={t('searchHistory')}
          className="w-full pl-10 pr-4 py-2.5 bg-white border border-[#163A2D]/20 rounded-2xl text-xs font-bold text-[#163A2D] focus:border-[#163A2D] outline-none shadow-2xs"
        />
      </div>

      {/* Filter Chips Bar */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none">
        {(['ALL', 'HEALTHY', 'DEFECTIVE', 'REVIEW'] as const).map((type) => (
          <button
            key={type}
            onClick={() => setFilterType(type)}
            className={`px-3.5 py-1.5 rounded-full text-xs font-bold shrink-0 transition-all cursor-pointer ${
              filterType === type
                ? 'bg-[#163A2D] text-white shadow-2xs'
                : 'bg-white border border-[#163A2D]/15 text-[#163A2D] hover:bg-[#F7F1E7]'
            }`}
          >
            {type === 'ALL'
              ? t('filterAll')
              : type === 'HEALTHY'
              ? t('filterHealthy')
              : type === 'DEFECTIVE'
              ? t('filterDefective')
              : t('filterReview')}
          </button>
        ))}
      </div>

      {/* Loading State */}
      {loading && (
        <div className="flex flex-col items-center justify-center p-12 text-center space-y-3">
          <Loader2 className="w-8 h-8 text-[#163A2D] animate-spin" />
          <p className="text-xs text-[#163A2D]/70 font-bold">Loading SQLite records...</p>
        </div>
      )}

      {/* Error / Offline Alert */}
      {error && !loading && (
        <div className="p-4 bg-white border border-rose-200 rounded-2xl text-xs text-[#E51E3A] space-y-1 shadow-2xs">
          <p className="font-bold">Notice</p>
          <p className="text-[11px] text-[#163A2D]/70">{error}</p>
        </div>
      )}

      {/* Empty State */}
      {!loading && filteredItems.length === 0 && (
        <div className="bg-white border border-[#163A2D]/10 rounded-3xl p-8 text-center space-y-3 shadow-2xs">
          <div className="w-12 h-12 bg-[#F7F1E7] rounded-2xl mx-auto flex items-center justify-center text-[#163A2D]/40">
            <History className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-sm font-black text-[#163A2D]">{t('noHistory')}</h3>
            <p className="text-xs text-[#163A2D]/60 mt-1">
              Start an inspection from the Home screen to record lot grades.
            </p>
          </div>
        </div>
      )}

      {/* Inspection Record List */}
      {!loading && (
        <div className="space-y-2">
          {filteredItems.map((item) => {
            const label = gradeToLabel(item.grading_result?.grade);
            const isHealthy = label === 'HEALTHY';
            const isReview = label === 'REVIEW';
            const confPct = item.confidence ? Math.round(item.confidence * 100) : null;

            return (
              <div
                key={item.inspection_id}
                onClick={() => onSelectInspection(item.inspection_id)}
                className="bg-white border border-[#163A2D]/10 p-3.5 rounded-3xl flex items-center justify-between shadow-2xs hover:border-[#163A2D]/30 active:scale-[0.99] transition-all cursor-pointer"
              >
                <div className="flex items-center gap-3">
                  {/* Color-coded icon */}
                  <div className={`w-9 h-9 rounded-2xl flex items-center justify-center shrink-0 ${
                    isHealthy ? 'bg-emerald-100' : isReview ? 'bg-amber-100' : 'bg-rose-100'
                  }`}>
                    {isHealthy
                      ? <CheckCircle2 className="w-5 h-5 text-emerald-700" />
                      : isReview
                      ? <AlertTriangle className="w-5 h-5 text-amber-700" />
                      : <XCircle className="w-5 h-5 text-[#E51E3A]" />
                    }
                  </div>

                  <div className="space-y-0.5">
                    {/* Primary: HEALTHY / DEFECTIVE */}
                    <div className="flex items-center gap-2">
                      <span className={`text-xs font-black uppercase ${
                        isHealthy ? 'text-emerald-700' : isReview ? 'text-amber-700' : 'text-[#E51E3A]'
                      }`}>
                        {label || 'INSPECTED'}
                      </span>
                      {/* Secondary: internal grade */}
                      <span className="text-[9px] font-bold text-[#163A2D]/40">
                        {item.grading_result?.grade || ''}
                      </span>
                    </div>

                    <div className="flex items-center gap-2 text-[10px] text-[#163A2D]/60 font-medium">
                      <span>{item.batch_id}</span>
                      <span>•</span>
                      <span>{new Date(item.started_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  {confPct !== null && (
                    <div className="text-right">
                      <span className="text-sm font-black text-[#163A2D] block">{confPct}%</span>
                      <span className="text-[8px] text-[#163A2D]/50 uppercase font-bold">Conf.</span>
                    </div>
                  )}
                  <ChevronRight className="w-4 h-4 text-[#163A2D]/40" />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
