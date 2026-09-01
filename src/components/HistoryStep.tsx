import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Database, Search, Building2, Calendar, CheckCircle2, AlertTriangle, XCircle, ChevronRight, Scale, RefreshCw } from 'lucide-react';
import { PastSessionLog, ScanResult } from '../types';

interface HistoryStepProps {
  onSelectReport: (result: ScanResult) => void;
  onPlayVoice: (text: string) => void;
}

export const HistoryStep: React.FC<HistoryStepProps> = ({
  onSelectReport,
  onPlayVoice,
}) => {
  const { t } = useTranslation();
  const [sessions, setSessions] = useState<PastSessionLog[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [searchQuery, setSearchQuery] = useState<string>('');

  const fetchSessions = async () => {
    setLoading(true);
    try {
      const res = await fetch('http://127.0.0.1:8000/api/v1/sessions');
      if (res.ok) {
        const data = await res.json();
        setSessions(data);
      } else {
        useFallbackSeedSessions();
      }
    } catch (err) {
      console.log('Using offline SQLite fallback sessions:', err);
      useFallbackSeedSessions();
    } finally {
      setLoading(false);
    }
  };

  const useFallbackSeedSessions = () => {
    const offlineSeed: PastSessionLog[] = [
      {
        id: 15,
        batch_id: 'BATCH-MH-2026-890',
        center_id: 'APMC-LASALGAON-MAIN-01',
        timestamp: '2026-09-01 09:45:12',
        filename: 'lot_lasalgaon_batch1.jpg',
        overall_grade: 'Grade-A',
        confidence_score: 96.5,
        grade_a_percentage: 82.4,
        grade_urs_percentage: 14.1,
        rejected_percentage: 3.5,
        damaged_count: 0, rotten_count: 0, sprouted_count: 0, undersized_count: 2,
        grade_a_weight_kg: 82.4, grade_urs_weight_kg: 14.1, rejected_weight_kg: 3.5, total_weight_kg: 100.0,
        moisture_level: '82% (Ideal)', firmness_rating: 'Solid & Crisp Shell', shelf_life_days: 60,
        farmer_recommendation: 'High-value export quality. Meets NAFED/APMC Grade-A criteria for long cold storage.'
      },
      {
        id: 14,
        batch_id: 'BATCH-MH-2026-883',
        center_id: 'APMC-NASHIK-CENTER-04',
        timestamp: '2026-09-01 04:30:00',
        filename: 'lot_nashik_export_04.jpg',
        overall_grade: 'Grade-URS',
        confidence_score: 93.8,
        grade_a_percentage: 44.5,
        grade_urs_percentage: 47.5,
        rejected_percentage: 8.0,
        damaged_count: 4, rotten_count: 1, sprouted_count: 0, undersized_count: 6,
        grade_a_weight_kg: 44.5, grade_urs_weight_kg: 47.5, rejected_weight_kg: 8.0, total_weight_kg: 100.0,
        moisture_level: '88% (Slightly High)', firmness_rating: 'Medium Firm', shelf_life_days: 25,
        farmer_recommendation: 'Meets SIH 2026 Under Relaxed Specifications (URS) norms. Sell in local market within 20 days.'
      },
      {
        id: 13,
        batch_id: 'BATCH-MH-2026-876',
        center_id: 'APMC-PUNE-MARKET-02',
        timestamp: '2026-08-31 22:15:00',
        filename: 'lot_pune_urs_spec.jpg',
        overall_grade: 'Grade-C',
        confidence_score: 94.2,
        grade_a_percentage: 22.0,
        grade_urs_percentage: 48.0,
        rejected_percentage: 30.0,
        damaged_count: 6, rotten_count: 4, sprouted_count: 5, undersized_count: 8,
        grade_a_weight_kg: 22.0, grade_urs_weight_kg: 48.0, rejected_weight_kg: 30.0, total_weight_kg: 100.0,
        moisture_level: '93% (High Rot Risk)', firmness_rating: 'Soft & Damp', shelf_life_days: 8,
        farmer_recommendation: 'Defect threshold exceeded. Separate affected onions immediately.'
      }
    ];
    setSessions(offlineSeed);
  };

  useEffect(() => {
    fetchSessions();
  }, []);

  const filteredSessions = sessions.filter(
    (s) =>
      s.batch_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.center_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.overall_grade.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleOpenReport = (session: PastSessionLog) => {
    let gradeType: 'A' | 'URS' | 'C' = 'A';
    if (session.overall_grade.includes('URS')) gradeType = 'URS';
    else if (session.overall_grade.includes('C')) gradeType = 'C';

    const result: ScanResult = {
      analysisId: f`LOG-${session.id}`,
      batchId: session.batch_id,
      centerId: session.center_id,
      grade: gradeType,
      overallGrade: session.overall_grade,
      qualityTitleKey: gradeType === 'A' ? 'gradeA' : gradeType === 'URS' ? 'gradeURS' : 'gradeC',
      score: Math.round(session.confidence_score),
      gradeAPercentage: session.grade_a_percentage,
      gradeURSPercentage: session.grade_urs_percentage,
      rejectedPercentage: session.rejected_percentage,
      defectFlags: {
        damaged: session.damaged_count > 0,
        damaged_count: session.damaged_count,
        rotten: session.rotten_count > 0,
        rotten_count: session.rotten_count,
        sprouted: session.sprouted_count > 0,
        sprouted_count: session.sprouted_count,
        undersized: session.undersized_count > 0,
        undersized_count: session.undersized_count,
      },
      weightDistribution: {
        total_batch_weight_kg: session.total_weight_kg,
        grade_a_weight_kg: session.grade_a_weight_kg,
        grade_urs_weight_kg: session.grade_urs_weight_kg,
        rejected_weight_kg: session.rejected_weight_kg,
        grade_a_weight_percentage: session.grade_a_percentage,
        grade_urs_weight_percentage: session.grade_urs_percentage,
        rejected_weight_percentage: session.rejected_percentage,
      },
      moisture: session.moisture_level,
      firmness: session.firmness_rating,
      shelfLife: `${session.shelf_life_days} Days`,
      defectSummary: `Damaged: ${session.damaged_count} • Rotten: ${session.rotten_count} • Sprouted: ${session.sprouted_count} • Undersized: ${session.undersized_count}`,
      recommendation: session.farmer_recommendation,
      imageUrl: '',
      timestamp: session.timestamp,
    };

    onPlayVoice(`Loading digital report for Batch ${session.batch_id}`);
    onSelectReport(result);
  };

  return (
    <div className="max-w-xl mx-auto px-4 py-6 space-y-6">
      {/* Top Banner */}
      <div className="bg-[#1E3A2B] text-white p-5 rounded-3xl border-3 border-[#3A7D44] shadow-lg space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-[#2D5A27] rounded-2xl border border-[#81C784]/40">
              <Database className="w-6 h-6 text-emerald-300" />
            </div>
            <div>
              <h2 className="text-xl font-black">{t('historyTitle')}</h2>
              <p className="text-xs text-emerald-200">{t('historySubtitle')}</p>
            </div>
          </div>

          <button
            onClick={fetchSessions}
            className="p-2.5 bg-[#2D5A27] hover:bg-[#3A7D44] text-white rounded-2xl border border-emerald-400/40"
            title="Refresh SQLite database logs"
          >
            <RefreshCw className="w-5 h-5 text-emerald-300" />
          </button>
        </div>

        <div className="pt-2 border-t border-emerald-700/60 flex items-center justify-between text-xs font-bold text-emerald-100">
          <span>{t('totalSessions')}:</span>
          <span className="bg-[#0F281E] px-3 py-1 rounded-full border border-emerald-500/40 text-emerald-300 font-mono">
            {sessions.length} Records Logged
          </span>
        </div>
      </div>

      {/* Search Bar */}
      <div className="relative">
        <Search className="w-5 h-5 text-stone-400 absolute left-4 top-1/2 -translate-y-1/2" />
        <input
          type="text"
          placeholder="Search by Batch ID or Procurement Center..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-12 pr-4 py-3.5 bg-white rounded-2xl border-2 border-stone-300 text-stone-900 font-bold text-sm focus:outline-none focus:border-[#2D5A27] shadow-sm"
        />
      </div>

      {/* Sessions Scrollable History Cards List */}
      {loading ? (
        <div className="py-12 text-center space-y-3">
          <div className="w-10 h-10 border-4 border-[#2D5A27] border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-sm font-bold text-stone-600">Loading SQLite grading history...</p>
        </div>
      ) : filteredSessions.length === 0 ? (
        <div className="bg-white p-8 rounded-3xl border-2 border-stone-200 text-center space-y-2">
          <span className="text-4xl">📜</span>
          <p className="font-extrabold text-stone-800">No matching grading logs found</p>
          <p className="text-xs text-stone-500">Try searching for a different Batch ID or Center</p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredSessions.map((session) => {
            const isGradeA = session.overall_grade.includes('Grade-A');
            const isGradeURS = session.overall_grade.includes('URS');

            return (
              <div
                key={session.id}
                onClick={() => handleOpenReport(session)}
                className={`p-5 rounded-3xl border-3 shadow-md hover:shadow-xl transition-all cursor-pointer space-y-3 active:scale-98 ${
                  session.status === 'DISPUTED'
                    ? 'bg-amber-50 border-amber-500 ring-2 ring-amber-400'
                    : 'bg-white border-stone-200 hover:border-[#2D5A27]'
                }`}
              >
                {/* Header Row */}
                <div className="flex items-center justify-between border-b pb-2.5 border-stone-100">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono font-black bg-[#1E3A2B] text-white px-2.5 py-1 rounded-lg">
                      {session.batch_id}
                    </span>
                    <span className="text-[11px] font-extrabold text-stone-500 flex items-center gap-1">
                      <Calendar className="w-3.5 h-3.5 text-stone-400" />
                      {session.timestamp}
                    </span>
                  </div>

                  <div className="flex items-center gap-1">
                    {session.status === 'DISPUTED' && (
                      <span className="bg-amber-500 text-stone-950 font-black text-[10px] px-2.5 py-1 rounded-full border border-amber-600 shadow-sm flex items-center gap-1">
                        <span>⚠️</span> DISPUTED
                      </span>
                    )}
                    <span
                      className={`px-3 py-1 rounded-full text-xs font-black flex items-center gap-1 shadow-sm ${
                        isGradeA
                          ? 'bg-emerald-100 text-emerald-900 border border-emerald-400'
                          : isGradeURS
                          ? 'bg-amber-100 text-amber-900 border border-amber-400'
                          : 'bg-rose-100 text-rose-900 border border-rose-400'
                      }`}
                    >
                      {isGradeA ? (
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-700" />
                      ) : isGradeURS ? (
                        <AlertTriangle className="w-3.5 h-3.5 text-amber-700" />
                      ) : (
                        <XCircle className="w-3.5 h-3.5 text-rose-700" />
                      )}
                      {session.overall_grade}
                    </span>
                  </div>
                </div>

                {/* Center & Confidence Row */}
                <div className="flex items-center justify-between text-xs font-bold text-stone-700">
                  <div className="flex items-center gap-1.5 text-stone-600">
                    <Building2 className="w-4 h-4 text-amber-600" />
                    <span>{session.center_id}</span>
                  </div>
                  <span className="text-emerald-800 font-extrabold bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                    AI SCORE {session.confidence_score}%
                  </span>
                </div>

                {/* Grade Distribution Bar */}
                <div className="space-y-1 pt-1">
                  <div className="flex justify-between text-[11px] font-extrabold">
                    <span className="text-emerald-800">Grade-A: {session.grade_a_percentage}%</span>
                    <span className="text-amber-800">Grade-URS: {session.grade_urs_percentage}%</span>
                    <span className="text-rose-800">Rejected: {session.rejected_percentage}%</span>
                  </div>
                  <div className="w-full bg-stone-100 h-2.5 rounded-full overflow-hidden flex border border-stone-200">
                    <div className="bg-emerald-600 h-full" style={{ width: `${session.grade_a_percentage}%` }} />
                    <div className="bg-amber-500 h-full" style={{ width: `${session.grade_urs_percentage}%` }} />
                    <div className="bg-rose-500 h-full" style={{ width: `${session.rejected_percentage}%` }} />
                  </div>
                </div>

                {/* Defect Summary Badges */}
                <div className="flex flex-wrap gap-1.5 pt-1 text-[10px] font-bold">
                  {session.damaged_count > 0 && (
                    <span className="bg-amber-50 text-amber-800 px-2 py-0.5 rounded-full border border-amber-200">
                      💥 Damaged: {session.damaged_count}
                    </span>
                  )}
                  {session.rotten_count > 0 && (
                    <span className="bg-rose-50 text-rose-800 px-2 py-0.5 rounded-full border border-rose-200">
                      🧪 Rotten: {session.rotten_count}
                    </span>
                  )}
                  {session.sprouted_count > 0 && (
                    <span className="bg-purple-50 text-purple-800 px-2 py-0.5 rounded-full border border-purple-200">
                      🌱 Sprouted: {session.sprouted_count}
                    </span>
                  )}
                  {session.undersized_count > 0 && (
                    <span className="bg-blue-50 text-blue-800 px-2 py-0.5 rounded-full border border-blue-200">
                      📏 Small: {session.undersized_count}
                    </span>
                  )}
                </div>

                {/* View Full Report Button */}
                <div className="pt-2 border-t border-stone-100 flex items-center justify-between text-xs font-black text-[#2D5A27]">
                  <span className="flex items-center gap-1">
                    <Scale className="w-4 h-4 text-emerald-600" />
                    <span>Total Batch: {session.total_weight_kg} KG</span>
                  </span>
                  <button className="flex items-center gap-1 bg-stone-100 hover:bg-[#2D5A27] hover:text-white px-3 py-1.5 rounded-xl border border-stone-300 transition-all">
                    <span>{t('viewReport')}</span>
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

function f(strings: TemplateStringsArray, ...values: any[]): string {
  return strings.reduce((acc, str, i) => acc + str + (values[i] ?? ''), '');
}
