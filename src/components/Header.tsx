import React, { useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { Volume2, WifiOff, Smartphone, ArrowLeft, Mic } from 'lucide-react';
import { AppRoute, LanguageCode } from '../types';

interface HeaderProps {
  currentStep: AppRoute;
  onSelectStep: (step: AppRoute) => void;
  onPlayVoice: (text: string) => void;
  onOpenVoiceCommand?: () => void;
  isOffline: boolean;
  canInstallPwa: boolean;
  onInstallPwa: () => void;
  onTogglePresenterToolbar?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  currentStep,
  onSelectStep,
  onPlayVoice,
  onOpenVoiceCommand,
  isOffline,
  canInstallPwa,
  onInstallPwa,
  onTogglePresenterToolbar,
}) => {
  const { t, i18n } = useTranslation();
  const tapCountRef = useRef<number>(0);
  const lastTapRef = useRef<number>(0);

  const handleLogoTap = () => {
    const now = Date.now();
    if (now - lastTapRef.current < 500) {
      tapCountRef.current += 1;
    } else {
      tapCountRef.current = 1;
    }
    lastTapRef.current = now;

    // Triple-tap opens developer/presenter toolbar
    if (tapCountRef.current >= 3) {
      tapCountRef.current = 0;
      if (onTogglePresenterToolbar) {
        onTogglePresenterToolbar();
      }
    }
  };

  const handleSelectLanguage = (lang: LanguageCode) => {
    i18n.changeLanguage(lang);
  };

  const handleHeaderBack = () => {
    if (currentStep === 'evidence' || currentStep === 'report') {
      onSelectStep('result');
    } else if (currentStep === 'capture' || currentStep === 'analyzing') {
      onSelectStep('new_inspection');
    } else if (currentStep === 'new_inspection' || currentStep === 'history' || currentStep === 'analytics' || currentStep === 'assistant' || currentStep === 'admin' || currentStep === 'result') {
      onSelectStep('home');
    } else {
      onSelectStep('landing');
    }
  };

  const currentLang = i18n.language ? i18n.language.substring(0, 2) : 'en';
  const showBackButton = currentStep !== 'home' && currentStep !== 'landing';

  return (
    <header className="bg-white/95 backdrop-blur-md sticky top-0 z-40 border-b border-[#163A2D]/10 shadow-2xs h-14 flex items-center font-sans">
      <div className="max-w-md mx-auto px-4 w-full flex items-center justify-between">
        {/* Left: Back button (if on sub-screen) & S.P.O.T. Logo */}
        <div className="flex items-center gap-2">
          {showBackButton && (
            <button
              onClick={handleHeaderBack}
              aria-label="Go Back"
              className="p-1.5 -ml-1.5 rounded-xl text-[#163A2D] hover:bg-[#163A2D]/10 active:scale-95 transition-transform"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
          )}
          <div
            onClick={handleLogoTap}
            className="flex items-center gap-2 cursor-pointer select-none"
          >
            <div className="w-8 h-8 rounded-xl bg-[#163A2D] text-white flex items-center justify-center text-sm shadow-2xs">
              🧅
            </div>
          <div>
            <div className="flex items-center gap-1.5 leading-none">
              <span className="text-sm font-black tracking-tight text-[#163A2D]">S.P.O.T.</span>
              <span className="text-[8px] font-black text-white bg-[#E51E3A] px-1.5 py-0.5 rounded">
                YOLO26
              </span>
            </div>
            <p className="text-[9px] text-[#163A2D]/70 font-bold mt-0.5">
              {t('appFullName')}
            </p>
          </div>
        </div>
      </div>

        {/* Right Controls: Language Selector & Audio Helper */}
        <div className="flex items-center gap-2">
          {/* Language Selector Chips */}
          <div className="bg-[#F7F1E7] border border-[#163A2D]/15 rounded-xl p-0.5 flex items-center gap-0.5">
            {(['en', 'hi', 'mr', 'ta'] as LanguageCode[]).map((langKey) => (
              <button
                key={langKey}
                onClick={() => handleSelectLanguage(langKey)}
                aria-label={`Switch to ${langKey.toUpperCase()}`}
                className={`px-2 py-1 rounded-lg text-[10px] font-extrabold uppercase transition-all ${
                  currentLang === langKey
                    ? 'bg-[#163A2D] text-white shadow-2xs scale-105'
                    : 'text-[#163A2D]/70 hover:text-[#163A2D]'
                }`}
              >
                {langKey}
              </button>
            ))}
          </div>

          {/* Voice Helper Speaker */}
          <button
            onClick={() => onPlayVoice(`${t('appName')}. ${t('appFullName')}. ${t('externalDisclaimer')}`)}
            aria-label="Listen Voice Guide"
            className="p-2 rounded-xl bg-[#F7F1E7] hover:bg-[#163A2D]/10 text-[#163A2D] border border-[#163A2D]/15 active:scale-95 transition-transform cursor-pointer"
            title={t('listenGuide')}
          >
            <Volume2 className="w-4 h-4 text-[#163A2D]" />
          </button>

          {/* Voice Command Microphone Button */}
          {onOpenVoiceCommand && (
            <button
              onClick={onOpenVoiceCommand}
              aria-label="Voice Command"
              className="p-2 rounded-xl bg-[#E51E3A] hover:bg-[#c91530] text-white shadow-xs active:scale-95 transition-transform flex items-center justify-center cursor-pointer"
              title="Voice Commands (Scan, History, Home, Upload)"
            >
              <Mic className="w-4 h-4 text-white" />
            </button>
          )}

          {/* PWA Install Button */}
          {canInstallPwa && (
            <button
              onClick={onInstallPwa}
              className="p-2 rounded-xl bg-[#E51E3A] text-white text-[9px] font-bold shadow-xs flex items-center gap-1 active:scale-95"
              title="Install App"
            >
              <Smartphone className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* Offline Banner Strip */}
      {isOffline && (
        <div className="absolute top-14 left-0 right-0 bg-[#E51E3A] text-white text-[10px] font-bold px-3 py-1 flex items-center justify-between shadow-xs">
          <div className="flex items-center gap-1.5">
            <WifiOff className="w-3 h-3" />
            <span>{t('offlineReady')}</span>
          </div>
          <span className="text-[9px] bg-white/20 px-1.5 py-0.2 rounded font-bold">Local SQLite</span>
        </div>
      )}
    </header>
  );
};
