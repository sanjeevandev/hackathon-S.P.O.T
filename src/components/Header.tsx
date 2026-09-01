import React, { useRef, useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Volume2, WifiOff, Smartphone, ShieldCheck, Award, Network } from 'lucide-react';
import { AppStep, LanguageCode } from '../types';
import { p2pSyncEngine } from '../utils/p2pSyncEngine';

interface HeaderProps {
  currentStep: AppStep;
  onSelectStep: (step: AppStep) => void;
  onPlayVoice: (text: string) => void;
  isOffline: boolean;
  canInstallPwa: boolean;
  onInstallPwa: () => void;
  judgeDemoMode?: boolean;
  onToggleJudgeDemoMode?: () => void;
  onTogglePresenterToolbar?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  currentStep,
  onSelectStep,
  onPlayVoice,
  isOffline,
  canInstallPwa,
  onInstallPwa,
  judgeDemoMode = false,
  onToggleJudgeDemoMode,
  onTogglePresenterToolbar,
}) => {
  const { t, i18n } = useTranslation();
  const tapCountRef = useRef<number>(0);
  const lastTapRef = useRef<number>(0);
  const longPressTimerRef = useRef<any>(null);
  const [peerCount, setPeerCount] = useState<number>(p2pSyncEngine.getPeerCount());

  useEffect(() => {
    const unsubscribe = p2pSyncEngine.subscribePeerCount((count) => {
      setPeerCount(count);
    });
    return () => unsubscribe();
  }, []);

  const handleTouchStartLogo = () => {
    longPressTimerRef.current = setTimeout(() => {
      if (onTogglePresenterToolbar) {
        onTogglePresenterToolbar();
      }
    }, 3000); // 3 seconds long-press
  };

  const handleTouchEndLogo = () => {
    if (longPressTimerRef.current) {
      clearTimeout(longPressTimerRef.current);
    }
  };

  const steps: Array<{ id: AppStep; label: string; icon: string }> = [
    { id: 'language', label: t('step1'), icon: '🌐' },
    { id: 'camera', label: t('step2'), icon: '📷' },
    { id: 'results', label: t('step3'), icon: '📄' },
    { id: 'history', label: t('step4'), icon: '📜' },
    { id: 'admin', label: 'Officer', icon: '👮' },
  ];

  const handleLogoTripleTap = () => {
    const now = Date.now();
    if (now - lastTapRef.current < 600) {
      tapCountRef.current += 1;
    } else {
      tapCountRef.current = 1;
    }
    lastTapRef.current = now;

    if (tapCountRef.current >= 3) {
      tapCountRef.current = 0;
      if (onToggleJudgeDemoMode) {
        onToggleJudgeDemoMode();
      }
    }
  };

  return (
    <header className="bg-[#1E3A2B] text-white shadow-xl sticky top-0 z-50 border-b-4 border-[#3A7D44]">
      <div className="max-w-xl mx-auto px-4 py-3">
        {/* S.P.O.T. Header & High-Contrast White Branding */}
        <div className="flex items-center justify-between gap-2 mb-3">
          <div
            onClick={handleLogoTripleTap}
            onMouseDown={handleTouchStartLogo}
            onMouseUp={handleTouchEndLogo}
            onTouchStart={handleTouchStartLogo}
            onTouchEnd={handleTouchEndLogo}
            className="flex items-center gap-3 cursor-pointer group select-none"
            title="Triple-tap: Judge Mode | Hold 3s: Presenter Controls"
            id="spot-logo-container"
          >
            <div className={`w-12 h-12 rounded-2xl flex items-center justify-center shadow-lg transform group-active:scale-90 transition-all border-2 ${
              judgeDemoMode
                ? 'bg-amber-500 border-amber-300 ring-4 ring-amber-400/50 animate-bounce'
                : 'bg-[#2D5A27] border-[#81C784] hover:scale-105'
            }`}>
              <span className="text-2xl" role="img" aria-label="spot-logo">
                {judgeDemoMode ? '👑' : '🧅'}
              </span>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl sm:text-2xl font-black tracking-wider text-white drop-shadow-md flex items-center gap-1.5">
                  S.P.O.T.
                </h1>
                {judgeDemoMode ? (
                  <span className="bg-amber-400 text-amber-950 text-[9px] sm:text-[10px] font-black px-2 py-0.5 rounded-full uppercase tracking-widest border border-amber-200 shadow-md animate-pulse">
                    👑 JUDGE DEMO MODE
                  </span>
                ) : (
                  <div className="flex items-center gap-1.5">
                    <span className="bg-[#8B5A2B] text-amber-100 text-[9px] sm:text-[10px] font-black px-2 py-0.5 rounded-full uppercase tracking-widest border border-amber-400/50 shadow-sm">
                      OFFLINE PWA
                    </span>
                    <span className="bg-emerald-950 text-emerald-200 text-[9px] sm:text-[10px] font-black px-2 py-0.5 rounded-full uppercase tracking-widest border border-emerald-500/50 shadow-sm flex items-center gap-1">
                      <Network className="w-3 h-3 text-emerald-400 animate-pulse" />
                      <span>Peer Mesh Connected ({peerCount} Devices)</span>
                    </span>
                  </div>
                )}
              </div>
              <p className="text-[11px] sm:text-xs text-[#81C784] font-bold tracking-tight">
                {judgeDemoMode ? 'SIH 2026 Judge Instant Evaluation Active' : t('subtitle')}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-1.5">
            {/* Quick Language Toggle Selector */}
            <div className="bg-[#0F281E] border border-[#3A7D44] rounded-xl px-1 py-1 flex items-center gap-0.5 text-xs shadow-inner">
              {(['hi', 'en', 'mr', 'ta'] as LanguageCode[]).map((langKey) => (
                <button
                  key={langKey}
                  onClick={() => i18n.changeLanguage(langKey)}
                  className={`px-1.5 py-0.5 rounded font-black uppercase text-[10px] transition-all ${
                    i18n.language === langKey
                      ? 'bg-[#81C784] text-[#0F281E] shadow ring-1 ring-white/50'
                      : 'text-emerald-200 hover:text-white'
                  }`}
                >
                  {langKey}
                </button>
              ))}
            </div>

            {/* Audio Voice Guide Button */}
            <button
              onClick={() => onPlayVoice(`S.P.O.T. ${t('subtitle')}`)}
              aria-label="Listen Voice"
              className="bg-[#2D5A27] hover:bg-[#3A7D44] active:scale-95 text-white p-2 rounded-xl border border-[#81C784]/60 shadow-md flex items-center justify-center transition-all"
              title={t('listenInstruction')}
            >
              <Volume2 className="w-4 h-4 text-emerald-300 animate-pulse" />
            </button>

            {/* PWA Install Trigger */}
            {canInstallPwa && (
              <button
                onClick={onInstallPwa}
                className="bg-[#8B5A2B] hover:bg-[#A86E3B] active:scale-95 text-white px-2.5 py-1.5 rounded-xl text-[10px] font-black flex items-center gap-1 border border-amber-300/40 shadow-md"
              >
                <Smartphone className="w-3.5 h-3.5 text-amber-200" />
                <span>{t('pwaInstall')}</span>
              </button>
            )}
          </div>
        </div>

        {/* Judge Demo Banner */}
        {judgeDemoMode && (
          <div className="mb-2 bg-gradient-to-r from-amber-600 via-yellow-600 to-amber-700 text-white px-3 py-1.5 rounded-xl text-xs flex items-center justify-between font-black border-2 border-amber-300 shadow-lg">
            <div className="flex items-center gap-2">
              <Award className="w-4 h-4 text-yellow-200 animate-bounce" />
              <span>👑 JUDGE EVALUATION MODE • 4 Instant Sample Batches Pre-Loaded</span>
            </div>
            <button
              onClick={onToggleJudgeDemoMode}
              className="text-[10px] bg-amber-950 text-amber-200 px-2 py-0.5 rounded-lg border border-amber-400 hover:bg-black"
            >
              Exit Demo
            </button>
          </div>
        )}

        {/* Offline Readiness Notification Banner */}
        {!judgeDemoMode && (isOffline ? (
          <div className="mb-2 bg-amber-900/90 text-amber-100 px-3 py-1 rounded-xl text-xs flex items-center justify-between font-extrabold border border-amber-500/50 shadow-md">
            <div className="flex items-center gap-2">
              <WifiOff className="w-4 h-4 text-amber-300 animate-pulse" />
              <span>{t('offlineNotice')}</span>
            </div>
            <span className="text-[10px] bg-black/40 px-2 py-0.5 rounded text-amber-200 uppercase">Field Mode</span>
          </div>
        ) : (
          <div className="mb-2 bg-[#0F281E]/80 text-emerald-200 px-3 py-1 rounded-xl text-[11px] flex items-center justify-between font-bold border border-emerald-500/30">
            <div className="flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              <span>S.P.O.T. ServiceWorker Active • Zero Internet Offline Ready</span>
            </div>
          </div>
        ))}

        {/* 4-Step Visual Progress Bar */}
        <div className="grid grid-cols-4 gap-1.5 bg-[#0F281E] p-1.5 rounded-2xl border border-[#2D5A27]">
          {steps.map((s) => {
            const isActive = currentStep === s.id;
            return (
              <button
                key={s.id}
                onClick={() => onSelectStep(s.id)}
                className={`py-1.5 px-1 rounded-xl text-[11px] font-extrabold flex items-center justify-center gap-1 transition-all ${
                  isActive
                    ? 'bg-[#3A7D44] text-white shadow-md ring-2 ring-[#81C784]'
                    : 'bg-transparent text-emerald-300/80 hover:bg-[#1E3A2B] hover:text-emerald-200'
                }`}
              >
                <span className="text-xs sm:text-sm">{s.icon}</span>
                <span className="truncate">{s.label}</span>
              </button>
            );
          })}
        </div>
      </div>
    </header>
  );
};
