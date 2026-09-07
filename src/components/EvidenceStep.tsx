import React, { useState } from 'react';
import { ArrowLeft, Eye } from 'lucide-react';
import { CanonicalInspectionResult } from '../types';

interface EvidenceStepProps {
  result: CanonicalInspectionResult;
  onBack: () => void;
}

export const EvidenceStep: React.FC<EvidenceStepProps> = ({
  result,
  onBack,
}) => {
  const onions = result.onions || [];
  const [selectedOnionId, setSelectedOnionId] = useState<string | null>(onions[0]?.onion_id || null);

  const selectedOnion = onions.find((o) => o.onion_id === selectedOnionId) || onions[0];

  return (
    <div className="max-w-2xl mx-auto px-4 py-6 space-y-6">
      {/* Navigation & Header */}
      <div className="flex items-center gap-3">
        <button
          onClick={onBack}
          className="p-2 rounded-xl border border-stone-200 hover:bg-stone-100 text-stone-700"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div>
          <h1 className="text-xl font-bold text-[#0F281E]">Evidence Overlay Viewer</h1>
          <p className="text-xs text-stone-500">Inspection ID: {result.inspection_id}</p>
        </div>
      </div>

      {/* Visual Bounding Box Canvas / Image Container */}
      <div className="bg-black rounded-3xl overflow-hidden aspect-[4/3] relative flex items-center justify-center border-4 border-[#2D5A27] shadow-lg">
        {/* Placeholder / Sample Image Display */}
        <div className="absolute inset-0 bg-gradient-to-br from-stone-800 to-stone-950 flex flex-col items-center justify-center p-4">
          <Eye className="w-12 h-12 text-emerald-400/80 mb-2 animate-pulse" />
          <span className="text-xs font-semibold text-stone-300">Sample Frame Bounding Overlay</span>
          <span className="text-[11px] text-stone-500 mt-1">{onions.length} Bulbs Detected</span>
        </div>

        {/* Bounding Box Overlays */}
        {onions.map((onion) => {
          const isSelected = onion.onion_id === selectedOnion?.onion_id;
          const [ymin, xmin, ymax, xmax] = onion.bounding_box;

          // Convert coordinates into approximate percentages for CSS relative layout
          const styleTop = `${(ymin / 720) * 100}%`;
          const styleLeft = `${(xmin / 1280) * 100}%`;
          const styleWidth = `${((xmax - xmin) / 1280) * 100}%`;
          const styleHeight = `${((ymax - ymin) / 720) * 100}%`;

          let strokeColor = 'border-emerald-500 bg-emerald-500/20';
          if (onion.final_status === 'DAMAGED' || onion.final_status === 'ROTTEN') {
            strokeColor = 'border-red-500 bg-red-500/25';
          } else if (onion.final_status === 'SPROUTED' || onion.final_status === 'UNDERSIZED') {
            strokeColor = 'border-amber-500 bg-amber-500/20';
          }

          return (
            <button
              key={onion.onion_id}
              onClick={() => setSelectedOnionId(onion.onion_id)}
              style={{ top: styleTop, left: styleLeft, width: styleWidth, height: styleHeight }}
              className={`absolute border-2 rounded-lg transition-all ${strokeColor} ${
                isSelected ? 'ring-4 ring-white shadow-2xl scale-[1.02] z-20' : 'opacity-80 hover:opacity-100 z-10'
              }`}
            >
              <span className="absolute -top-5 left-0 bg-[#0F281E] text-white text-[9px] font-bold px-1.5 py-0.5 rounded shadow">
                {onion.onion_id}
              </span>
            </button>
          );
        })}
      </div>

      {/* Multi-Onion Selector List */}
      <div className="space-y-2">
        <label className="block text-xs font-bold uppercase tracking-wider text-stone-600">
          Detected Onion Bulbs ({onions.length})
        </label>
        <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-none">
          {onions.map((onion) => (
            <button
              key={onion.onion_id}
              onClick={() => setSelectedOnionId(onion.onion_id)}
              className={`px-3 py-2 rounded-xl text-xs font-bold shrink-0 transition-all ${
                onion.onion_id === selectedOnion?.onion_id
                  ? 'bg-[#2D5A27] text-white shadow-md'
                  : 'bg-white border border-stone-200 text-stone-700 hover:bg-stone-50'
              }`}
            >
              {onion.onion_id} ({onion.final_status})
            </button>
          ))}
        </div>
      </div>

      {/* Selected Onion Evidence Details Panel */}
      {selectedOnion && (
        <div className="bg-white border border-stone-200 rounded-3xl p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-stone-100 pb-3">
            <div>
              <span className="text-[10px] uppercase font-bold text-stone-400">Bulb Identifier</span>
              <h3 className="text-base font-bold text-[#0F281E]">{selectedOnion.onion_id}</h3>
            </div>
            <span
              className={`px-3 py-1 rounded-full text-xs font-bold ${
                selectedOnion.final_status === 'HEALTHY'
                  ? 'bg-emerald-100 text-emerald-900'
                  : selectedOnion.final_status === 'DAMAGED' || selectedOnion.final_status === 'ROTTEN'
                  ? 'bg-red-100 text-red-900'
                  : 'bg-amber-100 text-amber-900'
              }`}
            >
              {selectedOnion.final_status}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="bg-stone-50 p-3 rounded-2xl border border-stone-200/60">
              <div className="text-stone-400 text-[10px] uppercase font-semibold">Detection Confidence</div>
              <div className="font-bold text-[#0F281E] text-sm mt-0.5">
                {(selectedOnion.detection_confidence * 100).toFixed(1)}%
              </div>
            </div>

            <div className="bg-stone-50 p-3 rounded-2xl border border-stone-200/60">
              <div className="text-stone-400 text-[10px] uppercase font-semibold">Size Measurement</div>
              <div className="font-bold text-stone-800 text-xs mt-0.5">
                {selectedOnion.size_estimate?.status === 'AVAILABLE' && selectedOnion.size_estimate.estimated_diameter_mm
                  ? `${selectedOnion.size_estimate.estimated_diameter_mm.toFixed(1)} mm`
                  : 'UNAVAILABLE (Uncalibrated)'}
              </div>
            </div>
          </div>

          {/* Probabilities Map */}
          <div className="space-y-2 text-xs">
            <div className="font-semibold text-stone-700">Defect Probability Distribution:</div>
            <div className="grid grid-cols-3 gap-2">
              <div className="p-2 bg-stone-50 rounded-xl border border-stone-200 text-center">
                <span className="text-[10px] text-stone-500 block">Damage</span>
                <span className="font-bold text-stone-800">
                  {((selectedOnion.defect_probabilities?.damage || 0) * 100).toFixed(0)}%
                </span>
              </div>
              <div className="p-2 bg-stone-50 rounded-xl border border-stone-200 text-center">
                <span className="text-[10px] text-stone-500 block">Rot</span>
                <span className="font-bold text-[#0F281E]">
                  {((selectedOnion.defect_probabilities?.rot || 0) * 100).toFixed(0)}%
                </span>
              </div>
              <div className="p-2 bg-stone-50 rounded-xl border border-stone-200 text-center">
                <span className="text-[10px] text-stone-500 block">Sprout</span>
                <span className="font-bold text-amber-700">
                  {((selectedOnion.defect_probabilities?.sprouting || 0) * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          </div>

          {/* Sub-region Visual Evidence List */}
          <div className="space-y-2 text-xs pt-2 border-t border-stone-100">
            <div className="font-semibold text-stone-700">Sub-Region Visual Evidence:</div>
            {selectedOnion.evidence_regions && selectedOnion.evidence_regions.length > 0 ? (
              <div className="space-y-1.5">
                {selectedOnion.evidence_regions.map((ev, i) => (
                  <div key={i} className="flex items-center justify-between p-2.5 bg-amber-50 border border-amber-200 rounded-xl">
                    <span className="font-medium text-amber-900">
                      Defect Region: {ev.defect_type}
                    </span>
                    <span className="font-bold text-amber-800">
                      {(ev.confidence * 100).toFixed(0)}% confidence
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-3 bg-stone-50 border border-stone-200 rounded-xl text-stone-500 text-xs italic">
                Visual evidence unavailable for this prediction.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
