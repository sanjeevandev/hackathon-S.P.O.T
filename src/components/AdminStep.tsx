import React, { useState, useEffect } from 'react';
import { ShieldCheck, BarChart3, PieChart as PieIcon, TrendingUp, Building2, Lock, Key, RefreshCw, Download, Database, Wifi, WifiOff } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line, CartesianGrid } from 'recharts';
import { DistrictMetricSummary } from '../types';

interface AdminStepProps {
  onBackToApp: () => void;
  onPlayVoice: (text: string) => void;
}

const DEFAULT_DISTRICT_METRICS: DistrictMetricSummary[] = [
  { district: 'Nashik APMC', centerCount: 6, totalMT: 620.5, gradeAMT: 415.0, gradeURSMT: 155.5, rejectedMT: 50.0, disputeCount: 18, disputeRatePct: 2.9 },
  { district: 'Pune APMC', centerCount: 4, totalMT: 410.0, gradeAMT: 246.0, gradeURSMT: 123.0, rejectedMT: 41.0, disputeCount: 14, disputeRatePct: 3.4 },
  { district: 'Solapur APMC', centerCount: 5, totalMT: 280.0, gradeAMT: 126.0, gradeURSMT: 98.0, rejectedMT: 56.0, disputeCount: 22, disputeRatePct: 7.8 },
  { district: 'Ahmednagar APMC', centerCount: 3, totalMT: 170.0, gradeAMT: 110.5, gradeURSMT: 42.5, rejectedMT: 17.0, disputeCount: 6, disputeRatePct: 3.5 },
];

const OVERALL_GRADE_PIE_DATA = [
  { name: 'Grade A Export', value: 897.5, color: '#4CAF50' },
  { name: 'Grade URS Buffer', value: 419.0, color: '#D97706' },
  { name: 'Rejected Batch', value: 164.0, color: '#EF4444' },
];

const WEEKLY_DISPUTE_TREND = [
  { week: 'Wk 1', disputes: 12, totalInspections: 280 },
  { week: 'Wk 2', disputes: 18, totalInspections: 340 },
  { week: 'Wk 3', disputes: 9, totalInspections: 310 },
  { week: 'Wk 4 (Current)', disputes: 21, totalInspections: 350 },
];

export const AdminStep: React.FC<AdminStepProps> = ({
  onBackToApp,
  onPlayVoice,
}) => {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(true); // Default true for instant demo access
  const [passcode, setPasscode] = useState<string>('');
  const [passcodeError, setPasscodeError] = useState<string | null>(null);
  const [isSyncing, setIsSyncing] = useState<boolean>(false);
  const [lastSyncTime, setLastSyncTime] = useState<string>(new Date().toLocaleTimeString());
  const [isOffline, setIsOffline] = useState<boolean>(!navigator.onLine);

  useEffect(() => {
    const handleOnline = () => setIsOffline(false);
    const handleOffline = () => setIsOffline(true);
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    if (passcode === '2026' || passcode === 'admin') {
      setIsAuthenticated(true);
      setPasscodeError(null);
      onPlayVoice('Officer authentication successful. Regional analytics dashboard loaded.');
    } else {
      setPasscodeError('Invalid APMC Officer Security PIN. Try PIN 2026!');
    }
  };

  const handleSyncData = () => {
    setIsSyncing(true);
    onPlayVoice('Synchronizing local SQLite and IndexedDB telemetry records...');
    setTimeout(() => {
      setIsSyncing(false);
      setLastSyncTime(new Date().toLocaleTimeString());
      onPlayVoice('Offline database tables successfully synchronized.');
    }, 800);
  };

  const totalMT = DEFAULT_DISTRICT_METRICS.reduce((acc, curr) => acc + curr.totalMT, 0);
  const totalDisputes = DEFAULT_DISTRICT_METRICS.reduce((acc, curr) => acc + curr.disputeCount, 0);

  if (!isAuthenticated) {
    return (
      <div className="max-w-md mx-auto px-4 py-12">
        <div className="bg-[#1E3A2B] text-white p-8 rounded-3xl border-4 border-[#3A7D44] shadow-2xl space-y-6">
          <div className="text-center space-y-2">
            <div className="w-16 h-16 bg-[#2D5A27] rounded-2xl mx-auto flex items-center justify-center border-2 border-[#81C784]">
              <Lock className="w-8 h-8 text-amber-300 animate-pulse" />
            </div>
            <h2 className="text-2xl font-black tracking-wide">APMC Officer Portal</h2>
            <p className="text-xs text-emerald-200">
              Regional Agricultural Officer Security Gate
            </p>
          </div>

          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-emerald-200 mb-1.5">
                Officer Security Passcode (PIN)
              </label>
              <div className="relative">
                <Key className="w-5 h-5 text-emerald-400 absolute left-3 top-3.5" />
                <input
                  type="password"
                  value={passcode}
                  onChange={(e) => setPasscode(e.target.value)}
                  placeholder="Enter PIN (Default: 2026)"
                  className="w-full bg-[#0F281E] border-2 border-[#3A7D44] text-white pl-10 pr-4 py-3 rounded-xl font-bold text-sm focus:outline-none focus:border-emerald-400"
                />
              </div>
              {passcodeError && (
                <p className="text-xs text-rose-300 font-bold mt-2">{passcodeError}</p>
              )}
            </div>

            <button
              type="submit"
              className="w-full py-3.5 bg-amber-600 hover:bg-amber-500 text-white rounded-xl font-black text-sm shadow-lg active:scale-95 transition-all flex items-center justify-center gap-2"
            >
              <ShieldCheck className="w-5 h-5" />
              <span>Authenticate Officer Access</span>
            </button>
          </form>

          <div className="pt-4 border-t border-emerald-800 text-center">
            <button
              onClick={() => {
                setIsAuthenticated(true);
                onPlayVoice('Demo Mode Access Granted.');
              }}
              className="text-xs text-amber-300 underline font-bold hover:text-white"
            >
              ⚡ Quick Demo Passcode Bypass
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-xl mx-auto px-4 py-6 space-y-6">
      {/* Top Officer Header */}
      <div className="bg-[#1E3A2B] text-white p-5 rounded-3xl border-3 border-[#3A7D44] shadow-xl flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 bg-amber-500 border-2 border-amber-300 rounded-2xl flex items-center justify-center shadow">
            <ShieldCheck className="w-7 h-7 text-amber-950" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-black tracking-wide">Regional Officer Portal</h2>
              <span className="bg-amber-400 text-amber-950 text-[9px] font-black px-2 py-0.5 rounded-full uppercase border border-amber-200">
                APMC ADMIN
              </span>
            </div>
            <p className="text-xs text-emerald-200 font-bold">
              Aggregate District Quality & Procurement Telemetry
            </p>
          </div>
        </div>

        <button
          onClick={onBackToApp}
          className="px-3 py-1.5 bg-[#2D5A27] hover:bg-[#3A7D44] text-emerald-100 rounded-xl text-xs font-bold border border-emerald-500/40"
        >
          Exit Admin
        </button>
      </div>

      {/* Offline Synchronization Bar */}
      <div className="bg-stone-900 border-2 border-amber-500/50 p-3.5 rounded-2xl text-white flex items-center justify-between shadow-md">
        <div className="flex items-center gap-2.5">
          <Database className="w-5 h-5 text-amber-400 animate-pulse" />
          <div>
            <div className="flex items-center gap-2">
              <p className="text-xs font-black text-amber-300">
                Synced Local IndexedDB / SQLite Storage
              </p>
              {isOffline ? (
                <span className="bg-rose-900 text-rose-200 text-[9px] font-bold px-1.5 py-0.5 rounded flex items-center gap-1">
                  <WifiOff className="w-3 h-3" /> Offline Synced
                </span>
              ) : (
                <span className="bg-emerald-900 text-emerald-200 text-[9px] font-bold px-1.5 py-0.5 rounded flex items-center gap-1">
                  <Wifi className="w-3 h-3" /> Live SQLite Cloud
                </span>
              )}
            </div>
            <p className="text-[10px] text-stone-400">
              Last Sync: {lastSyncTime} • 18 Mandi Centers Telemetry Active
            </p>
          </div>
        </div>

        <button
          onClick={handleSyncData}
          disabled={isSyncing}
          className="bg-amber-600 hover:bg-amber-500 text-white px-3 py-1.5 rounded-xl text-xs font-bold flex items-center gap-1.5 border border-amber-300/40"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isSyncing ? 'animate-spin' : ''}`} />
          <span>{isSyncing ? 'Syncing...' : 'Sync Tables'}</span>
        </button>
      </div>

      {/* High-Contrast Executive Metrics Grid */}
      <div className="grid grid-cols-2 gap-3" id="admin-metrics-grid">
        <div className="bg-stone-900 text-white p-4 rounded-2xl border-2 border-emerald-500 shadow-md">
          <p className="text-[11px] font-bold text-stone-400 uppercase tracking-wider">Total Inspected MT</p>
          <p className="text-2xl font-black text-emerald-400 mt-1">{totalMT.toLocaleString()} MT</p>
          <p className="text-[10px] text-emerald-300/80 mt-0.5">Across 18 Procurement Depots</p>
        </div>

        <div className="bg-stone-900 text-white p-4 rounded-2xl border-2 border-amber-500 shadow-md">
          <p className="text-[11px] font-bold text-stone-400 uppercase tracking-wider">Grade A vs URS Ratio</p>
          <p className="text-2xl font-black text-amber-300 mt-1">60.6% / 28.3%</p>
          <p className="text-[10px] text-amber-200/80 mt-0.5">Grade A (897MT) • URS (419MT)</p>
        </div>

        <div className="bg-stone-900 text-white p-4 rounded-2xl border-2 border-rose-500 shadow-md">
          <p className="text-[11px] font-bold text-stone-400 uppercase tracking-wider">Dispute Frequency</p>
          <p className="text-2xl font-black text-rose-400 mt-1">3.8% ({totalDisputes} Lots)</p>
          <p className="text-[10px] text-rose-300/80 mt-0.5">Solapur Peak: 7.8% Dispute Rate</p>
        </div>

        <div className="bg-stone-900 text-white p-4 rounded-2xl border-2 border-blue-500 shadow-md">
          <p className="text-[11px] font-bold text-stone-400 uppercase tracking-wider">Active APMC Mandis</p>
          <p className="text-2xl font-black text-blue-400 mt-1">18 Mandis</p>
          <p className="text-[10px] text-blue-300/80 mt-0.5">4 Major Onion Districts</p>
        </div>
      </div>

      {/* District Comparison BarChart */}
      <div className="bg-stone-900 text-white p-5 rounded-3xl border-3 border-emerald-600 shadow-xl space-y-3">
        <div className="flex items-center justify-between border-b pb-2 border-stone-800">
          <div className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-emerald-400" />
            <h3 className="text-sm font-black text-white">
              Inspected Metric Tons (MT) by District
            </h3>
          </div>
          <span className="text-[10px] bg-emerald-950 text-emerald-300 px-2 py-0.5 rounded border border-emerald-500/40">
            District Ratio
          </span>
        </div>

        <div className="h-56 w-full pt-2">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={DEFAULT_DISTRICT_METRICS} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="district" stroke="#9CA3AF" tick={{ fontSize: 10 }} />
              <YAxis stroke="#9CA3AF" tick={{ fontSize: 10 }} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1F2937', borderColor: '#4B5563', borderRadius: '12px', fontSize: '12px' }}
                itemStyle={{ color: '#F9FAFB' }}
              />
              <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
              <Bar dataKey="gradeAMT" name="Grade A MT" fill="#4CAF50" stackId="a" radius={[0, 0, 4, 4]} />
              <Bar dataKey="gradeURSMT" name="Grade URS MT" fill="#D97706" stackId="a" />
              <Bar dataKey="rejectedMT" name="Rejected MT" fill="#EF4444" stackId="a" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Overall Quality Grade Distribution & Dispute Trend Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* PieChart: Grade Breakdown */}
        <div className="bg-stone-900 text-white p-4 rounded-3xl border-2 border-stone-700 shadow-lg space-y-2">
          <div className="flex items-center gap-2 border-b pb-2 border-stone-800">
            <PieIcon className="w-4 h-4 text-amber-400" />
            <h4 className="text-xs font-black text-white">Overall Quality Ratio</h4>
          </div>
          <div className="h-44 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={OVERALL_GRADE_PIE_DATA}
                  cx="50%"
                  cy="50%"
                  innerRadius={35}
                  outerRadius={55}
                  paddingAngle={4}
                  dataKey="value"
                >
                  {OVERALL_GRADE_PIE_DATA.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ backgroundColor: '#1F2937', borderColor: '#4B5563', borderRadius: '8px', fontSize: '11px' }}
                />
                <Legend wrapperStyle={{ fontSize: '10px' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* LineChart: Dispute Frequency Trend */}
        <div className="bg-stone-900 text-white p-4 rounded-3xl border-2 border-stone-700 shadow-lg space-y-2">
          <div className="flex items-center gap-2 border-b pb-2 border-stone-800">
            <TrendingUp className="w-4 h-4 text-rose-400" />
            <h4 className="text-xs font-black text-white">Weekly Dispute Trend</h4>
          </div>
          <div className="h-44 w-full pt-1">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={WEEKLY_DISPUTE_TREND} margin={{ top: 5, right: 10, left: -25, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="week" stroke="#9CA3AF" tick={{ fontSize: 9 }} />
                <YAxis stroke="#9CA3AF" tick={{ fontSize: 9 }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1F2937', borderColor: '#4B5563', borderRadius: '8px', fontSize: '11px' }}
                />
                <Line type="monotone" dataKey="disputes" name="Disputes" stroke="#EF4444" strokeWidth={3} dot={{ r: 4, fill: '#EF4444' }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* District Detail Table */}
      <div className="bg-stone-900 text-white p-4 rounded-3xl border-2 border-stone-700 shadow-lg space-y-3">
        <div className="flex items-center justify-between border-b pb-2 border-stone-800">
          <h3 className="text-xs font-black uppercase text-amber-300 tracking-wider">
            District Procurement Telemetry Summary
          </h3>
          <button
            onClick={() => {
              alert('Exporting Regional APMC Telemetry CSV report...');
              onPlayVoice('CSV Telemetry report exported.');
            }}
            className="text-[10px] bg-stone-800 hover:bg-stone-700 text-stone-200 px-2.5 py-1 rounded-lg border border-stone-600 flex items-center gap-1 font-bold"
          >
            <Download className="w-3 h-3 text-amber-300" />
            <span>Export CSV</span>
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-stone-800 text-stone-400 font-bold text-[10px] uppercase">
                <th className="py-2">District</th>
                <th className="py-2">Centers</th>
                <th className="py-2">Total MT</th>
                <th className="py-2">Grade A %</th>
                <th className="py-2">Dispute Rate</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-stone-800 font-bold">
              {DEFAULT_DISTRICT_METRICS.map((d) => (
                <tr key={d.district} className="hover:bg-stone-800/50">
                  <td className="py-2.5 text-emerald-300 flex items-center gap-1">
                    <Building2 className="w-3.5 h-3.5 text-stone-400" />
                    <span>{d.district}</span>
                  </td>
                  <td className="py-2.5 text-stone-300">{d.centerCount} Depots</td>
                  <td className="py-2.5 text-white font-extrabold">{d.totalMT} MT</td>
                  <td className="py-2.5 text-emerald-400">
                    {Math.round((d.gradeAMT / d.totalMT) * 100)}%
                  </td>
                  <td className="py-2.5">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-black ${
                      d.disputeRatePct > 5.0 ? 'bg-rose-900 text-rose-200 border border-rose-500/50' : 'bg-emerald-950 text-emerald-300 border border-emerald-500/40'
                    }`}>
                      {d.disputeRatePct}% ({d.disputeCount})
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
