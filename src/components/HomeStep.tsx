import React from 'react';
import { Camera, History, ShieldAlert, CheckCircle2, ArrowRight } from 'lucide-react';
import { AppRoute } from '../types';

interface HomeStepProps {
  onNavigate: (route: AppRoute) => void;
  onStartNewInspection: () => void;
}

export const HomeStep: React.FC<HomeStepProps> = ({
  onNavigate,
  onStartNewInspection,
}) => {
  return (
    <div className="max-w-2xl mx-auto px-4 py-6 space-y-6">
      {/* Operational Header Hero */}
      <div className="bg-[#0F281E] text-white rounded-3xl p-6 shadow-xl relative overflow-hidden">
        <div className="relative z-10 space-y-3">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-[#2D5A27] bg-opacity-60 border border-green-500/30 rounded-full text-xs font-semibold text-emerald-300">
            <ShieldAlert className="w-3.5 h-3.5" />
            <span>APMC Procurement Grade Evaluation</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight">Onion Quality Inspection</h1>
          <p className="text-sm text-stone-300">
            Standardized optical quality screening & lot percentage evaluation for APMC onion procurement.
          </p>
        </div>
      </div>

      {/* Primary Operational Actions */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <button
          onClick={onStartNewInspection}
          className="flex flex-col items-start justify-between p-5 bg-[#2D5A27] text-white rounded-2xl shadow-md hover:bg-[#23471F] transition-all active:scale-[0.99] min-h-[140px] text-left group"
        >
          <div className="p-3 bg-white/10 rounded-xl">
            <Camera className="w-6 h-6 text-emerald-300" />
          </div>
          <div className="space-y-1 mt-4">
            <div className="text-lg font-bold flex items-center gap-2">
              New Inspection
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </div>
            <p className="text-xs text-emerald-100">Capture sample lot image for quality grading</p>
          </div>
        </button>

        <button
          onClick={() => onNavigate('history')}
          className="flex flex-col items-start justify-between p-5 bg-white text-[#0F281E] border border-stone-200 rounded-2xl shadow-sm hover:border-stone-300 transition-all active:scale-[0.99] min-h-[140px] text-left group"
        >
          <div className="p-3 bg-stone-100 rounded-xl">
            <History className="w-6 h-6 text-[#2D5A27]" />
          </div>
          <div className="space-y-1 mt-4">
            <div className="text-lg font-bold flex items-center gap-2">
              View History
              <ArrowRight className="w-4 h-4 text-stone-400 group-hover:translate-x-1 transition-transform" />
            </div>
            <p className="text-xs text-stone-500">Access stored inspection records & reports</p>
          </div>
        </button>
      </div>

      {/* Scope Disclaimer & Status */}
      <div className="bg-stone-100 border border-stone-200 rounded-2xl p-4 space-y-2 text-xs text-stone-600">
        <div className="font-semibold text-stone-800 flex items-center gap-1.5">
          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          <span>Operational Standard Disclaimer</span>
        </div>
        <p>
          All lot statistics are evaluated under status <strong>SAMPLE_ONLY</strong> based strictly on photographed sample bulbs. Surface RGB imaging does not detect unphotographed or internal rot.
        </p>
      </div>
    </div>
  );
};
