import React from 'react';
import { useTranslation } from 'react-i18next';
import { Camera, History, ShieldCheck, Sparkles, WifiOff, Info, ArrowRight } from 'lucide-react';
import { LanguageCode } from '../types';

interface LandingPageProps {
  onStartInspection: () => void;
  onViewHistory: () => void;
  onContinue?: () => void;
  onEnterDashboard?: () => void;
  isOffline?: boolean;
}

export const LandingPage: React.FC<LandingPageProps> = ({
  onStartInspection,
  onViewHistory,
  isOffline = false,
}) => {
  const { t, i18n } = useTranslation();

  const handleSelectLanguage = (lang: LanguageCode) => {
    i18n.changeLanguage(lang);
  };

  const currentLang = i18n.language ? i18n.language.substring(0, 2) : 'en';

  return (
    <div className="min-h-screen w-full bg-[#F7F1E7] text-[#163A2D] flex flex-col justify-between font-sans select-none overflow-x-hidden">
      {/* Top Bar with Brand & Controls */}
      <div className="w-full max-w-md mx-auto px-5 pt-6 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-xl bg-[#163A2D] text-white flex items-center justify-center text-base shadow-sm">
            🧅
          </div>
          <span className="text-lg font-black tracking-tight text-[#163A2D]">S.P.O.T.</span>
        </div>
        
        <div className="flex items-center gap-2">
          {/* Language Selector Chips */}
          <div className="bg-white border border-[#163A2D]/15 rounded-xl p-0.5 flex items-center gap-0.5 shadow-2xs">
            {(['en', 'hi', 'mr', 'ta'] as LanguageCode[]).map((langKey) => (
              <button
                key={langKey}
                onClick={() => handleSelectLanguage(langKey)}
                aria-label={`Switch to ${langKey.toUpperCase()}`}
                className={`px-2 py-0.5 rounded-lg text-[10px] font-extrabold uppercase transition-all ${
                  currentLang === langKey
                    ? 'bg-[#163A2D] text-white shadow-2xs scale-105'
                    : 'text-[#163A2D]/70 hover:text-[#163A2D]'
                }`}
              >
                {langKey}
              </button>
            ))}
          </div>

          {/* Offline indicator — only when actually offline */}
          {isOffline && (
            <div className="inline-flex items-center gap-1.5 px-2 py-1 bg-white border border-[#E51E3A]/40 rounded-xl text-[10px] font-bold text-[#E51E3A] shadow-2xs">
              <WifiOff className="w-3 h-3" />
              <span>Offline</span>
            </div>
          )}
        </div>
      </div>

      {/* Main Hero Container - Perfectly Centered for 360-430px */}
      <div className="w-full max-w-md mx-auto px-5 py-6 flex-1 flex flex-col items-center justify-center text-center space-y-6">
        {/* Emblem & AI Badge */}
        <div className="flex flex-col items-center space-y-3">
          <div className="relative">
            <div className="w-24 h-24 sm:w-28 sm:h-28 rounded-3xl bg-[#163A2D] text-white flex items-center justify-center shadow-xl border-2 border-[#163A2D]">
              <svg
                viewBox="0 0 100 100"
                className="w-14 h-14 sm:w-16 sm:h-16"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
              >
                {/* Outer Shell */}
                <path
                  d="M50 14C30 14 18 32 18 54C18 74 30 86 50 86C70 86 82 74 82 54C82 32 70 14 50 14Z"
                  stroke="#F7F1E7"
                  strokeWidth="4"
                  strokeLinecap="round"
                />
                {/* Internal Layer */}
                <path
                  d="M50 24C36 24 28 36 28 54C28 68 36 76 50 76C64 76 72 68 72 54C72 36 64 24 50 24Z"
                  stroke="#F7F1E7"
                  strokeWidth="3"
                  strokeDasharray="4 3"
                  strokeLinecap="round"
                />
                {/* Stem & Core */}
                <path
                  d="M50 14V8M44 8H56"
                  stroke="#F7F1E7"
                  strokeWidth="4"
                  strokeLinecap="round"
                />
                <circle cx="50" cy="54" r="5" fill="#E51E3A" />
              </svg>
            </div>
            
            <div className="absolute -bottom-2 -right-2 bg-[#E51E3A] text-white p-1.5 rounded-xl shadow-md border-2 border-[#F7F1E7]">
              <Sparkles className="w-4 h-4" />
            </div>
          </div>

          <div className="inline-flex items-center gap-1 px-3 py-0.5 bg-[#163A2D]/10 rounded-full text-[10px] font-extrabold uppercase tracking-wider text-[#163A2D]">
            <ShieldCheck className="w-3 h-3 text-[#163A2D]" />
            <span>{t('opticalAiGrading')}</span>
          </div>
        </div>

        {/* Title & Description */}
        <div className="space-y-2 max-w-xs">
          <h1 className="text-2xl sm:text-3xl font-black tracking-tight text-[#163A2D] leading-tight">
            {t('landingTitle')}
          </h1>
          <p className="text-xs sm:text-sm text-[#163A2D]/75 font-medium leading-relaxed">
            {t('landingSubtitle')}
          </p>
        </div>

        {/* Primary & Secondary Action CTAs */}
        <div className="w-full space-y-3 pt-2">
          <button
            onClick={onStartInspection}
            className="w-full min-h-[52px] py-4 px-6 bg-[#E51E3A] hover:bg-[#c91530] active:scale-[0.98] text-white rounded-2xl font-black shadow-lg transition-all flex items-center justify-between text-sm uppercase tracking-wider group"
          >
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-xl bg-white/20 flex items-center justify-center">
                <Camera className="w-4 h-4" />
              </div>
              <span>{t('startInspection')}</span>
            </div>
            <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
          </button>

          <button
            onClick={onViewHistory}
            className="w-full min-h-[46px] py-3 px-5 bg-white hover:bg-white/80 active:scale-[0.98] text-[#163A2D] border border-[#163A2D]/20 rounded-2xl font-bold text-xs shadow-2xs transition-all flex items-center justify-center gap-2"
          >
            <History className="w-4 h-4 text-[#163A2D]/70" />
            <span>{t('viewHistory')}</span>
          </button>
        </div>

        {/* Scope Disclaimer Box */}
        <div className="w-full bg-white border border-[#163A2D]/15 rounded-2xl p-3.5 text-left flex items-start gap-2.5 shadow-2xs">
          <Info className="w-4 h-4 text-[#E51E3A] shrink-0 mt-0.5" />
          <p className="text-[11px] text-[#163A2D]/80 font-medium leading-snug">
            <strong>{t('externalDisclaimer')}</strong>
          </p>
        </div>
      </div>

      {/* Footer Tag */}
      <div className="w-full max-w-md mx-auto px-5 pb-6 text-center">
        <p className="text-[10px] text-[#163A2D]/50 font-bold uppercase tracking-widest">
          {t('appTagline')}
        </p>
      </div>
    </div>
  );
};
