import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { ArrowLeft, ArrowRight, Info } from 'lucide-react';
import { NewInspectionMeta } from '../types';

interface NewInspectionStepProps {
  onBack: () => void;
  onProceed: (meta: NewInspectionMeta) => void;
}

export const NewInspectionStep: React.FC<NewInspectionStepProps> = ({
  onBack,
  onProceed,
}) => {
  const { t } = useTranslation();
  const [batchId, setBatchId] = useState<string>('BATCH-MH-NASHIK-01');
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
    <div className="max-w-md mx-auto px-4 py-5 space-y-5 pb-24 font-sans text-[#163A2D]">
      <div className="flex items-center gap-3">
        <button
          onClick={onBack}
          className="p-2 rounded-xl border border-[#163A2D]/15 bg-white text-[#163A2D] active:scale-95 transition-all shadow-2xs cursor-pointer"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div>
          <h1 className="text-xl font-black text-[#163A2D]">{t('lotIntake')}</h1>
          <p className="text-xs text-[#163A2D]/70">Enter lot metadata before optical scan</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="bg-white border border-[#163A2D]/15 rounded-3xl p-5 shadow-2xs space-y-4">
        {/* Lot ID */}
        <div className="space-y-1.5">
          <label className="text-xs font-black text-[#163A2D] uppercase tracking-wide">
            {t('batchIdLabel')}
          </label>
          <input
            type="text"
            required
            value={batchId}
            onChange={(e) => setBatchId(e.target.value)}
            placeholder="e.g. BATCH-MH-NASHIK-01"
            className="w-full px-3.5 py-3 rounded-2xl bg-[#F7F1E7] border border-[#163A2D]/20 focus:border-[#163A2D] outline-none text-sm font-bold text-[#163A2D]"
          />
        </div>

        {/* Supplier */}
        <div className="space-y-1.5">
          <label className="text-xs font-black text-[#163A2D] uppercase tracking-wide">
            {t('supplierLabel')}
          </label>
          <input
            type="text"
            required
            value={supplier}
            onChange={(e) => setSupplier(e.target.value)}
            placeholder="e.g. Nashik Farmers Producer Co."
            className="w-full px-3.5 py-3 rounded-2xl bg-[#F7F1E7] border border-[#163A2D]/20 focus:border-[#163A2D] outline-none text-sm font-bold text-[#163A2D]"
          />
        </div>

        {/* Procurement Center */}
        <div className="space-y-1.5">
          <label className="text-xs font-black text-[#163A2D] uppercase tracking-wide">
            {t('centerIdLabel')}
          </label>
          <select
            value={centerId}
            onChange={(e) => setCenterId(e.target.value)}
            className="w-full px-3.5 py-3 rounded-2xl bg-[#F7F1E7] border border-[#163A2D]/20 focus:border-[#163A2D] outline-none text-sm font-bold text-[#163A2D]"
          >
            <option value="APMC-NASHIK-CENTER-04">Nashik Main Mandi (Center 04)</option>
            <option value="APMC-LASALGAON-01">Lasalgaon Onion Market (Center 01)</option>
            <option value="APMC-PIMPALGAON-02">Pimpalgaon Baswant (Center 02)</option>
            <option value="APMC-PUNE-MARKET-03">Pune Gultekdi Mandi (Center 03)</option>
          </select>
        </div>

        {/* Declared Lot Weight */}
        <div className="space-y-1.5">
          <label className="text-xs font-black text-[#163A2D] uppercase tracking-wide">
            Declared Weight (Optional kg)
          </label>
          <input
            type="number"
            min="1"
            step="0.5"
            value={weightKg}
            onChange={(e) => setWeightKg(e.target.value)}
            placeholder="e.g. 500"
            className="w-full px-3.5 py-3 rounded-2xl bg-[#F7F1E7] border border-[#163A2D]/20 focus:border-[#163A2D] outline-none text-sm font-bold text-[#163A2D]"
          />
        </div>

        {/* Notes */}
        <div className="space-y-1.5">
          <label className="text-xs font-black text-[#163A2D] uppercase tracking-wide">
            Intake Remarks (Optional)
          </label>
          <input
            type="text"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="e.g. Visual quality sampling check"
            className="w-full px-3.5 py-3 rounded-2xl bg-[#F7F1E7] border border-[#163A2D]/20 focus:border-[#163A2D] outline-none text-sm font-bold text-[#163A2D]"
          />
        </div>

        {/* Sampling Scope Notice */}
        <div className="p-3.5 bg-[#F7F1E7] border border-[#163A2D]/10 rounded-2xl flex items-start gap-2.5">
          <Info className="w-4 h-4 text-[#163A2D] shrink-0 mt-0.5" />
          <p className="text-[11px] text-[#163A2D]/80 leading-relaxed font-medium">
            <strong>Sampling Protocol:</strong> S.P.O.T. evaluates one representative onion sample per scan for external optical classification.
          </p>
        </div>

        {/* Primary CTA */}
        <button
          type="submit"
          className="w-full min-h-[50px] py-3.5 bg-[#E51E3A] hover:bg-[#c91530] text-white rounded-2xl font-black text-xs uppercase tracking-wider shadow-md active:scale-95 transition-all flex items-center justify-center gap-2 cursor-pointer"
        >
          <span>{t('proceedToCamera')}</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
};
