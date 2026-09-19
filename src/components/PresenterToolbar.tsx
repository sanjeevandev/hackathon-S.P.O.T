import React, { useState } from 'react';
import { RefreshCw, X, Sliders, CheckCircle, Globe, Server } from 'lucide-react';
import { getApiUrl, setApiUrl, resetApiUrl } from '../api/client';

interface PresenterToolbarProps {
  isVisible: boolean;
  onClose: () => void;
  onResetDemo: () => void;
  isServerAiMode?: boolean;
  onToggleAiMode?: () => void;
  onSimulateHardware?: () => void;
}

export const PresenterToolbar: React.FC<PresenterToolbarProps> = ({
  isVisible,
  onClose,
  onResetDemo,
}) => {
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [customUrl, setCustomUrl] = useState<string>(getApiUrl());
  const [showApiConfig, setShowApiConfig] = useState<boolean>(false);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 2500);
  };

  const handleSaveUrl = () => {
    if (customUrl.trim()) {
      setApiUrl(customUrl.trim());
      showToast(`API Base URL saved: ${customUrl.trim()}`);
      setShowApiConfig(false);
    }
  };

  const handleResetUrl = () => {
    resetApiUrl();
    setCustomUrl(getApiUrl());
    showToast(`API URL reset to default (${getApiUrl()})`);
    setShowApiConfig(false);
  };

  if (!isVisible) return null;

  return (
    <div className="fixed bottom-4 right-4 z-[9999] bg-[#163A2D] text-white p-3.5 rounded-2xl border border-white/20 shadow-2xl backdrop-blur-md max-w-xs animate-in slide-in-from-bottom duration-300 font-sans">
      {/* Toast Overlay */}
      {toastMessage && (
        <div className="absolute -top-12 left-0 right-0 bg-[#E51E3A] text-white text-[11px] font-black py-1.5 px-3 rounded-xl text-center shadow-lg flex items-center justify-center gap-1.5">
          <CheckCircle className="w-3.5 h-3.5" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Header */}
      <div className="flex items-center justify-between border-b border-white/10 pb-2 mb-2">
        <div className="flex items-center gap-1.5">
          <Sliders className="w-4 h-4 text-[#E51E3A]" />
          <h3 className="text-xs font-black text-white uppercase tracking-wider">
            Quick Tools & Config
          </h3>
        </div>
        <button
          onClick={onClose}
          className="text-white/60 hover:text-white p-1 rounded-lg transition"
          title="Close (Shift + P)"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Quick Actions */}
      <div className="space-y-2">
        <button
          onClick={() => {
            onResetDemo();
            showToast('Reset to New Inspection Intake!');
          }}
          className="w-full bg-white/10 hover:bg-white/20 text-white p-2.5 rounded-xl border border-white/10 flex items-center justify-between text-xs font-bold transition-all active:scale-95"
        >
          <div className="flex items-center gap-2">
            <RefreshCw className="w-4 h-4 text-[#E51E3A]" />
            <span>Reset Workflow</span>
          </div>
          <span className="text-[9px] bg-white/20 text-white px-1.5 py-0.5 rounded">Intake</span>
        </button>

        <button
          onClick={() => setShowApiConfig(!showApiConfig)}
          className="w-full bg-white/10 hover:bg-white/20 text-white p-2.5 rounded-xl border border-white/10 flex items-center justify-between text-xs font-bold transition-all active:scale-95"
        >
          <div className="flex items-center gap-2">
            <Server className="w-4 h-4 text-emerald-400" />
            <span>Backend API URL</span>
          </div>
          <span className="text-[9px] bg-emerald-500/20 text-emerald-300 px-1.5 py-0.5 rounded truncate max-w-[90px]">
            {getApiUrl().replace('http://', '').replace('https://', '')}
          </span>
        </button>

        {showApiConfig && (
          <div className="p-2.5 bg-black/30 rounded-xl border border-white/10 space-y-2 text-xs">
            <div>
              <label className="text-[10px] text-white/70 font-semibold block mb-1">
                Backend Endpoint URL
              </label>
              <div className="relative">
                <Globe className="w-3.5 h-3.5 text-white/40 absolute left-2.5 top-2.5" />
                <input
                  type="text"
                  value={customUrl}
                  onChange={(e) => setCustomUrl(e.target.value)}
                  placeholder="http://192.168.1.X:8000"
                  className="w-full bg-white/10 border border-white/20 rounded-lg pl-8 pr-2 py-1.5 text-xs text-white placeholder-white/40 focus:outline-none focus:border-emerald-400 font-mono"
                />
              </div>
            </div>
            <div className="flex items-center gap-1.5 pt-1">
              <button
                onClick={handleSaveUrl}
                className="flex-1 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg font-bold text-[11px] transition"
              >
                Apply
              </button>
              <button
                onClick={handleResetUrl}
                className="py-1 px-2 bg-white/10 hover:bg-white/20 text-white/80 rounded-lg font-medium text-[11px] transition"
              >
                Default
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
