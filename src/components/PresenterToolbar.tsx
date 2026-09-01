import React, { useState } from 'react';
import { RefreshCw, Cpu, Printer, X, Sliders, CheckCircle, Zap } from 'lucide-react';

interface PresenterToolbarProps {
  isVisible: boolean;
  onClose: () => void;
  onResetDemo: () => void;
  isServerAiMode: boolean;
  onToggleAiMode: () => void;
  onSimulateHardware: () => void;
}

export const PresenterToolbar: React.FC<PresenterToolbarProps> = ({
  isVisible,
  onClose,
  onResetDemo,
  isServerAiMode,
  onToggleAiMode,
  onSimulateHardware,
}) => {
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 2500);
  };

  if (!isVisible) return null;

  return (
    <div className="fixed bottom-4 right-4 z-[9999] bg-stone-950 text-white p-3.5 rounded-2xl border-2 border-amber-400 shadow-2xl backdrop-blur-md max-w-xs animate-in slide-in-from-bottom duration-300">
      {/* Toast Overlay */}
      {toastMessage && (
        <div className="absolute -top-12 left-0 right-0 bg-emerald-600 text-white text-[11px] font-black py-1.5 px-3 rounded-xl text-center shadow-lg border border-emerald-300 flex items-center justify-center gap-1.5 animate-bounce">
          <CheckCircle className="w-3.5 h-3.5" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Header */}
      <div className="flex items-center justify-between border-b border-stone-800 pb-2 mb-2">
        <div className="flex items-center gap-1.5">
          <Sliders className="w-4 h-4 text-amber-400 animate-spin" style={{ animationDuration: '6s' }} />
          <h3 className="text-xs font-black text-amber-300 uppercase tracking-wider">
            Presenter Stall Control
          </h3>
        </div>
        <button
          onClick={onClose}
          className="text-stone-400 hover:text-white p-1 rounded-lg hover:bg-stone-800 transition"
          title="Close Presenter Controls (Shift + P)"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      <p className="text-[10px] text-stone-400 mb-2.5 font-medium">
        Quick stall controls for SIH judges presentation setup.
      </p>

      {/* 3 Quick Action Buttons */}
      <div className="space-y-2">
        {/* Action 1: Reset Demo State */}
        <button
          onClick={() => {
            onResetDemo();
            showToast('Demo State Cleared ➔ Returned to Step 1!');
          }}
          className="w-full bg-stone-800 hover:bg-stone-700 text-stone-100 p-2 rounded-xl border border-stone-700 flex items-center justify-between text-xs font-bold transition-all active:scale-95"
        >
          <div className="flex items-center gap-2">
            <RefreshCw className="w-4 h-4 text-amber-400" />
            <span>Reset Demo State</span>
          </div>
          <span className="text-[9px] bg-stone-900 text-stone-400 px-1.5 py-0.5 rounded">Step 1</span>
        </button>

        {/* Action 2: Force AI Detection Mode */}
        <button
          onClick={() => {
            onToggleAiMode();
            showToast(isServerAiMode ? 'Switched to Edge ONNX WASM Mode!' : 'Forced Server OpenCV/YOLOv8 Mode!');
          }}
          className={`w-full p-2 rounded-xl border flex items-center justify-between text-xs font-bold transition-all active:scale-95 ${
            isServerAiMode
              ? 'bg-sky-950 border-sky-500 text-sky-200'
              : 'bg-emerald-950 border-emerald-500 text-emerald-200'
          }`}
        >
          <div className="flex items-center gap-2">
            <Cpu className="w-4 h-4" />
            <span>{isServerAiMode ? 'Mode: Server YOLOv8' : 'Mode: Edge ONNX WASM'}</span>
          </div>
          <Zap className="w-3.5 h-3.5 fill-current" />
        </button>

        {/* Action 3: Simulate Scale & Printer */}
        <button
          onClick={() => {
            onSimulateHardware();
            showToast('Simulated 25.4 kg Scale & ESC/POS Print!');
          }}
          className="w-full bg-stone-800 hover:bg-stone-700 text-stone-100 p-2 rounded-xl border border-stone-700 flex items-center justify-between text-xs font-bold transition-all active:scale-95"
        >
          <div className="flex items-center gap-2">
            <Printer className="w-4 h-4 text-emerald-400" />
            <span>Simulate Scale (25.4kg) & Print</span>
          </div>
          <span className="text-[9px] bg-emerald-900 text-emerald-300 px-1.5 py-0.5 rounded font-black">25.4 kg</span>
        </button>
      </div>

      <div className="mt-2.5 pt-2 border-t border-stone-800 text-[9px] text-stone-500 text-center font-bold">
        Hotkey: <kbd className="bg-stone-800 px-1 py-0.5 rounded text-amber-300">Shift + P</kbd> • Logo Hold 3s
      </div>
    </div>
  );
};
