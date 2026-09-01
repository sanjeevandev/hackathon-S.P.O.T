import React, { useState, useEffect } from 'react';
import { Scale, Wifi, AlertCircle, Edit3, CheckCircle2, RefreshCw } from 'lucide-react';
import { WebSerialScaleManager, SerialScaleStatus, ScaleReadout } from '../utils/webSerialScale';

interface ScaleIntakeWidgetProps {
  currentWeightKg: number;
  onWeightChange: (weightKg: number) => void;
}

export const ScaleIntakeWidget: React.FC<ScaleIntakeWidgetProps> = ({
  currentWeightKg,
  onWeightChange,
}) => {
  const [scaleManager] = useState(() => new WebSerialScaleManager());
  const [scaleStatus, setScaleStatus] = useState<SerialScaleStatus>('disconnected');
  const [statusMessage, setStatusMessage] = useState<string>('');
  const [isManualEntry, setIsManualEntry] = useState<boolean>(false);
  const [manualInputVal, setManualInputVal] = useState<string>(currentWeightKg.toString());
  const [validationError, setValidationError] = useState<string | null>(null);
  const [rawPayload, setRawPayload] = useState<string>('');

  const handleConnectScale = async () => {
    await scaleManager.connect(
      (readout: ScaleReadout) => {
        onWeightChange(readout.weightKg);
        setRawPayload(readout.rawString);
      },
      (status, msg) => {
        setScaleStatus(status);
        if (msg) setStatusMessage(msg);
      }
    );
  };

  useEffect(() => {
    return () => {
      scaleManager.disconnect();
    };
  }, [scaleManager]);

  const handleManualValueChange = (valStr: string) => {
    setManualInputVal(valStr);
    const val = parseFloat(valStr);
    if (isNaN(val)) {
      setValidationError('Please enter a valid numeric weight in KG');
    } else if (val < 10 || val > 5000) {
      setValidationError('Weight out of bounds! Valid lot range: 10.0 KG to 5000.0 KG');
    } else {
      setValidationError(null);
      onWeightChange(val);
    }
  };

  return (
    <div className="bg-[#0F281E] text-white p-5 rounded-3xl border-3 border-[#3A7D44] shadow-xl space-y-4">
      {/* Header Bar */}
      <div className="flex items-center justify-between border-b pb-3 border-emerald-700/60">
        <div className="flex items-center gap-2.5">
          <div className="p-2 bg-[#1E3A2B] rounded-xl border border-emerald-500/40">
            <Scale className="w-5 h-5 text-emerald-300" />
          </div>
          <div>
            <h3 className="text-sm font-black text-white uppercase tracking-wider">
              RS-232 / USB Digital Scale Sync
            </h3>
            <span className="text-[10px] text-emerald-300 font-bold block">
              Web Serial API Live Batch Intake
            </span>
          </div>
        </div>

        {/* Manual Fallback Toggle */}
        <button
          onClick={() => setIsManualEntry(!isManualEntry)}
          className={`px-3 py-1.5 rounded-full text-xs font-extrabold flex items-center gap-1.5 transition-all border ${
            isManualEntry
              ? 'bg-amber-500 text-stone-950 border-amber-400'
              : 'bg-[#1E3A2B] text-emerald-300 border-emerald-500/40 hover:bg-[#2D5A27]'
          }`}
        >
          <Edit3 className="w-3.5 h-3.5" />
          <span>{isManualEntry ? 'Manual Entry Active' : 'Manual Toggle'}</span>
        </button>
      </div>

      {/* Main Weight Display Area */}
      {!isManualEntry ? (
        <div className="bg-[#1A382B] p-4 rounded-2xl border-2 border-emerald-500/40 text-center space-y-2">
          {/* Status Badge */}
          <div className="flex items-center justify-between text-xs font-bold px-2">
            <span className="flex items-center gap-1.5 text-stone-300 text-[11px]">
              <Wifi className={`w-3.5 h-3.5 ${scaleStatus === 'streaming' ? 'text-emerald-400 animate-pulse' : 'text-stone-400'}`} />
              <span>RS-232 Port: 9600 Baud</span>
            </span>

            <span
              className={`px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase ${
                scaleStatus === 'streaming'
                  ? 'bg-emerald-500 text-stone-950 animate-pulse'
                  : scaleStatus === 'connecting'
                  ? 'bg-amber-500 text-stone-950'
                  : 'bg-stone-700 text-stone-300'
              }`}
            >
              {scaleStatus === 'streaming' ? '● LIVE SYNC' : scaleStatus}
            </span>
          </div>

          {/* Oversized Green Numerical Typography */}
          <div className="py-2">
            <div className="text-5xl font-black font-mono tracking-tight text-[#00FF66] drop-shadow-[0_0_12px_rgba(0,255,102,0.4)] flex items-baseline justify-center gap-2">
              <span>{currentWeightKg.toFixed(1)}</span>
              <span className="text-2xl font-sans text-emerald-300 font-bold">KG</span>
            </div>
            <span className="text-[10px] text-emerald-200/80 font-bold uppercase tracking-widest block mt-1">
              Auto-Populated Inspection Batch Weight
            </span>
          </div>

          {/* Action Connect Button */}
          {scaleStatus !== 'streaming' && (
            <button
              onClick={handleConnectScale}
              className="w-full py-3 px-4 bg-[#2D5A27] hover:bg-[#3A7D44] active:scale-95 text-white font-extrabold text-xs rounded-xl border border-emerald-400/50 shadow-md flex items-center justify-center gap-2"
            >
              <RefreshCw className="w-4 h-4 text-emerald-300" />
              <span>Connect RS-232 Digital Scale (Web Serial)</span>
            </button>
          )}

          {rawPayload && (
            <div className="text-[9px] font-mono text-emerald-400/70 pt-1">
              RAW ASCII: <code className="bg-[#0F281E] px-1.5 py-0.5 rounded">{rawPayload}</code>
            </div>
          )}
        </div>
      ) : (
        /* Manual Input Fallback Mode */
        <div className="bg-[#1A382B] p-4 rounded-2xl border-2 border-amber-500/40 space-y-3">
          <div className="flex items-center justify-between text-xs text-amber-300 font-bold">
            <span>Manual Lot Weight Entry</span>
            <span className="text-[10px] text-stone-300">Valid Bounds: 10 - 5000 KG</span>
          </div>

          <div className="relative flex items-center">
            <input
              type="number"
              step="0.1"
              min="10"
              max="5000"
              value={manualInputVal}
              onChange={(e) => handleManualValueChange(e.target.value)}
              className="w-full bg-stone-900 border-2 border-amber-400 text-[#00FF66] text-3xl font-mono font-black py-3 px-4 rounded-xl focus:outline-none focus:ring-2 focus:ring-amber-400"
            />
            <span className="absolute right-4 text-xl font-bold text-emerald-300">KG</span>
          </div>

          {validationError ? (
            <div className="flex items-center gap-1.5 text-xs text-rose-300 font-bold bg-rose-950/80 p-2 rounded-xl border border-rose-500/40">
              <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
              <span>{validationError}</span>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 text-xs text-emerald-300 font-bold">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>Valid inspection batch weight ready for backend payload</span>
            </div>
          )}
        </div>
      )}

      {statusMessage && (
        <p className="text-[10px] text-stone-300 font-bold text-center bg-[#1E3A2B] p-1.5 rounded-lg border border-emerald-500/20">
          {statusMessage}
        </p>
      )}
    </div>
  );
};
