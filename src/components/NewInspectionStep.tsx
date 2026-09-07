import React, { useState } from 'react';
import { ArrowLeft, Check, Info } from 'lucide-react';
import { NewInspectionMeta } from '../types';

interface NewInspectionStepProps {
  onBack: () => void;
  onProceed: (meta: NewInspectionMeta) => void;
}

export const NewInspectionStep: React.FC<NewInspectionStepProps> = ({
  onBack,
  onProceed,
}) => {
  const [batchId, setBatchId] = useState<string>(`BATCH-MH-NASHIK-${Math.floor(1000 + Math.random() * 9000)}`);
  const [supplier, setSupplier] = useState<string>('Nashik Farmers Producer Co.');
  const [centerId, setCenterId] = useState<string>('APMC-NASHIK-CENTER-04');
  const [weightKg, setWeightKg] = useState<string>('');
  const [notes, setNotes] = useState<string>('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onProceed({
      batch_id: batchId.trim() || `BATCH-${Date.now()}`,
      supplier: supplier.trim() || 'Unknown Supplier',
      procurement_center_id: centerId,
      declared_weight_kg: weightKg ? parseFloat(weightKg) : undefined,
      notes: notes.trim() || undefined,
      sampling_status: 'SAMPLE_ONLY',
    });
  };

  return (
    <div className="max-w-xl mx-auto px-4 py-6 space-y-6">
      <div className="flex items-center gap-3">
        <button
          onClick={onBack}
          className="p-2 rounded-xl border border-stone-200 hover:bg-stone-100 text-stone-700"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div>
          <h1 className="text-xl font-bold text-[#0F281E]">New Batch Inspection</h1>
          <p className="text-xs text-stone-500">Provide lot metadata before image intake</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="bg-white border border-stone-200 rounded-3xl p-6 shadow-sm space-y-5">
        <div>
          <label className="block text-xs font-semibold uppercase text-stone-600 mb-1.5">
            Batch Identifier *
          </label>
          <input
            type="text"
            required
            value={batchId}
            onChange={(e) => setBatchId(e.target.value)}
            className="w-full px-3.5 py-2.5 rounded-xl border border-stone-300 text-sm focus:ring-2 focus:ring-[#2D5A27] focus:outline-none"
            placeholder="e.g. BATCH-MH-NASHIK-4921"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold uppercase text-stone-600 mb-1.5">
            Supplier / Mandi Licensee *
          </label>
          <input
            type="text"
            required
            value={supplier}
            onChange={(e) => setSupplier(e.target.value)}
            className="w-full px-3.5 py-2.5 rounded-xl border border-stone-300 text-sm focus:ring-2 focus:ring-[#2D5A27] focus:outline-none"
            placeholder="Supplier name or FPO"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold uppercase text-stone-600 mb-1.5">
            APMC Procurement Center
          </label>
          <select
            value={centerId}
            onChange={(e) => setCenterId(e.target.value)}
            className="w-full px-3.5 py-2.5 rounded-xl border border-stone-300 text-sm bg-white focus:ring-2 focus:ring-[#2D5A27] focus:outline-none"
          >
            <option value="APMC-NASHIK-CENTER-04">APMC Nashik Main Yard (Center 04)</option>
            <option value="APMC-LASALGAON-CENTER-01">APMC Lasalgaon Procurement Center 01</option>
            <option value="APMC-PIMPALGAON-CENTER-02">APMC Pimpalgaon Yard 02</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold uppercase text-stone-600 mb-1.5">
            Declared Batch Weight (KG) — Optional
          </label>
          <input
            type="number"
            step="0.1"
            min="0.1"
            value={weightKg}
            onChange={(e) => setWeightKg(e.target.value)}
            className="w-full px-3.5 py-2.5 rounded-xl border border-stone-300 text-sm focus:ring-2 focus:ring-[#2D5A27] focus:outline-none"
            placeholder="e.g. 500.0"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold uppercase text-stone-600 mb-1.5">
            Notes / Observations — Optional
          </label>
          <textarea
            rows={2}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            className="w-full px-3.5 py-2.5 rounded-xl border border-stone-300 text-sm focus:ring-2 focus:ring-[#2D5A27] focus:outline-none"
            placeholder="Special lot conditions or truck number..."
          />
        </div>

        {/* Scope Indicator */}
        <div className="flex items-start gap-2.5 p-3.5 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-900">
          <Info className="w-4 h-4 text-emerald-700 shrink-0 mt-0.5" />
          <div>
            <span className="font-bold">Scope Constraint:</span> Inspection operates strictly under <strong>SAMPLE_ONLY</strong> sampling mode. Unphotographed physical lot volume is not inferred.
          </div>
        </div>

        <button
          type="submit"
          className="w-full py-3.5 px-4 bg-[#2D5A27] text-white rounded-2xl font-bold shadow-md hover:bg-[#23471F] transition-all flex items-center justify-center gap-2"
        >
          <span>Proceed to Camera Capture</span>
          <Check className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
};
