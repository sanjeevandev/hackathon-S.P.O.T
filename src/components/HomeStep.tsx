import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Camera, History, ArrowRight, ShieldCheck, CheckCircle2, AlertCircle, Info, ChevronRight, XCircle, AlertTriangle } from 'lucide-react';
import { AppRoute, HistoryItem } from '../types';
import { getInspectionHistory } from '../api/inspections';

function gradeToLabel(grade?: string): 'HEALTHY' | 'DEFECTIVE' | 'REVIEW' | null {
  if (!grade) return null;
  if (grade === 'Grade-A' || grade === 'A') return 'HEALTHY';
  if (grade === 'Grade-URS' || grade === 'URS') return 'REVIEW';
  if (grade === 'Grade-C' || grade === 'C' || grade === 'REJECTED') return 'DEFECTIVE';
  return null;
}

interface HomeStepProps {
  onNavigate: (route: AppRoute) => void;
  onStartNewInspection: () => void;
}

export const HomeStep: React.FC<HomeStepProps> = ({
  onNavigate,
  onStartNewInspection,
}) => {
  const { t } = useTranslation();
  const [recentHistory, setRecentHistory] = useState<HistoryItem[]>([]);
  const [, setLoadingHistory] = useState<boolean>(true);

  useEffect(() => {
    async function loadData() {
      try {
        const data = await getInspectionHistory();
        setRecentHistory(data);
      } catch (err) {
        console.warn('Failed to load recent history on home', err);
      } finally {
        setLoadingHistory(false);
      }
    }
    loadData();
  }, []);

  // Compute real counts from SQLite history
  const totalScans = recentHistory.length;
  let healthyCount = 0;
  let defectiveCount = 0;

  recentHistory.forEach((item) => {
    const grade = item.grading_result?.grade;
    const label = gradeToLabel(grade);
    if (label === 'HEALTHY') {
      healthyCount += 1;
    } else if (label === 'DEFECTIVE') {
      defectiveCount += 1;
    }
  });

  return (
    <div className="max-w-md mx-auto px-4 py-5 space-y-5 pb-24 font-sans text-[#163A2D]">
      {/* Hero Action Card */}
      <div className="bg-[#163A2D] text-white rounded-3xl p-5 shadow-md border border-[#163A2D] space-y-4">
        <div className="space-y-1">
          <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 bg-white/10 rounded-full text-[9px] font-bold tracking-wide uppercase text-white/90 border border-white/10">
            <ShieldCheck className="w-3 h-3 text-emerald-400" />
            <span>{t('opticalAiGrading')}</span>
          </div>
          <h2 className="text-xl font-black tracking-tight text-white leading-tight">
            {t('newScanPrompt')}
          </h2>
          <p className="text-xs text-white/80 leading-relaxed max-w-[280px]">
            {t('newScanDesc')}
          </p>
        </div>

        {/* Primary CTA Button: SCAN ONION */}
        <div className="space-y-2 pt-1">
          <button
            onClick={onStartNewInspection}
            className="w-full min-h-[50px] py-3.5 px-4 bg-[#E51E3A] hover:bg-[#c91530] active:scale-[0.98] text-white rounded-2xl font-black shadow-lg transition-all flex items-center justify-between group uppercase text-xs tracking-wider cursor-pointer"
          >
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-xl bg-white/20 text-white flex items-center justify-center">
                <Camera className="w-4 h-4" />
              </div>
              <span>{t('startInspection')}</span>
            </div>
            <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
          </button>

          <button
            onClick={() => onNavigate('history')}
            className="w-full py-2.5 px-3 bg-white/10 hover:bg-white/20 active:scale-[0.98] text-white rounded-xl font-bold text-xs transition-all flex items-center justify-center gap-1.5 border border-white/10 cursor-pointer"
          >
            <History className="w-3.5 h-3.5" />
            <span>{t('viewHistory')}</span>
          </button>
        </div>

        {/* Scope Indicators */}
        <div className="pt-2 border-t border-white/10 grid grid-cols-2 gap-2 text-[10px]">
          <div className="bg-black/15 px-2.5 py-1.5 rounded-xl border border-white/10 flex items-center justify-between">
            <span className="text-white/80">Surface quality:</span>
            <span className="font-bold text-emerald-300 uppercase">Assessed</span>
          </div>
          <div className="bg-black/15 px-2.5 py-1.5 rounded-xl border border-white/10 flex items-center justify-between">
            <span className="text-white/80">Internal rot:</span>
            <span className="font-bold text-amber-300 uppercase">Out of Scope</span>
          </div>
        </div>
      </div>

      {/* Real Statistics Summary Cards */}
      <div className="grid grid-cols-3 gap-2 text-center">
        <div className="bg-white p-3 rounded-2xl border border-[#163A2D]/10 shadow-2xs">
          <span className="text-[10px] font-bold text-[#163A2D]/70 uppercase block">
            {t('totalInspected')}
          </span>
          <span className="text-xl font-black text-[#163A2D] mt-0.5 block">
            {totalScans}
          </span>
        </div>

        <div className="bg-white p-3 rounded-2xl border border-[#163A2D]/10 shadow-2xs">
          <span className="text-[10px] font-bold text-[#163A2D]/70 uppercase block">
            {t('healthyCount')}
          </span>
          <span className="text-xl font-black text-[#163A2D] mt-0.5 block flex items-center justify-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 inline" />
            {healthyCount}
          </span>
        </div>

        <div className="bg-white p-3 rounded-2xl border border-[#163A2D]/10 shadow-2xs">
          <span className="text-[10px] font-bold text-[#163A2D]/70 uppercase block">
            {t('defectiveCount')}
          </span>
          <span className="text-xl font-black text-[#E51E3A] mt-0.5 block flex items-center justify-center gap-1">
            <AlertCircle className="w-3.5 h-3.5 text-[#E51E3A] inline" />
            {defectiveCount}
          </span>
        </div>
      </div>

      {/* Scope Disclaimer Banner */}
      <div className="p-3.5 bg-white border border-[#163A2D]/15 rounded-2xl flex items-start gap-2.5 shadow-2xs">
        <Info className="w-4 h-4 text-[#E51E3A] shrink-0 mt-0.5" />
        <p className="text-[11px] text-[#163A2D]/80 leading-tight font-medium">
          <strong>{t('externalDisclaimer')}</strong>
        </p>
      </div>

      {/* Recent Inspections List */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-black uppercase tracking-wider text-[#163A2D]">
            {t('recentScans')}
          </h3>
          {recentHistory.length > 0 && (
            <button
              onClick={() => onNavigate('history')}
              className="text-[11px] font-bold text-[#E51E3A] flex items-center gap-0.5"
            >
              <span>{t('filterAll')}</span>
              <ChevronRight className="w-3 h-3" />
            </button>
          )}
        </div>

        {recentHistory.length === 0 ? (
          <div className="bg-white border border-[#163A2D]/10 rounded-2xl p-6 text-center space-y-2 shadow-2xs">
            <div className="w-10 h-10 bg-[#F7F1E7] rounded-xl mx-auto flex items-center justify-center text-[#163A2D]/50">
              <History className="w-5 h-5" />
            </div>
            <p className="text-xs font-bold text-[#163A2D]/70">{t('noHistory')}</p>
            <p className="text-[10px] text-[#163A2D]/50">
              Start your first inspection above to log quality grades in SQLite.
            </p>
          </div>
        ) : (
          <div className="space-y-1.5">
            {recentHistory.slice(0, 3).map((item) => {
              const label = gradeToLabel(item.grading_result?.grade);
              const isHealthy = label === 'HEALTHY';
              const isReview = label === 'REVIEW';
              return (
                <div
                  key={item.inspection_id}
                  onClick={() => onNavigate('history')}
                  className="bg-white border border-[#163A2D]/10 p-3 rounded-2xl flex items-center justify-between shadow-2xs hover:border-[#163A2D]/30 transition-all cursor-pointer"
                >
                  <div className="flex items-center gap-2.5">
                    <div className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 ${
                      isHealthy ? 'bg-emerald-100' : isReview ? 'bg-amber-100' : 'bg-rose-100'
                    }`}>
                      {isHealthy
                        ? <CheckCircle2 className="w-4 h-4 text-emerald-700" />
                        : isReview
                        ? <AlertTriangle className="w-4 h-4 text-amber-700" />
                        : <XCircle className="w-4 h-4 text-[#E51E3A]" />
                      }
                    </div>
                    <div>
                      <div className={`text-xs font-black uppercase ${
                        isHealthy ? 'text-emerald-700' : isReview ? 'text-amber-700' : 'text-[#E51E3A]'
                      }`}>
                        {label || 'INSPECTED'}
                      </div>
                      <p className="text-[10px] text-[#163A2D]/60 font-medium">
                        {item.batch_id} · {item.grading_result?.grade || ''}
                      </p>
                    </div>
                  </div>
                  <ChevronRight className="w-4 h-4 text-[#163A2D]/40" />
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Protected Officer Entry (Discreet Secondary Footer Link) */}
      <div className="pt-2 text-center">
        <button
          onClick={() => onNavigate('admin')}
          className="text-[11px] text-[#163A2D]/60 hover:text-[#163A2D] font-bold underline"
        >
          {t('officer')}
        </button>
      </div>
    </div>
  );
};
