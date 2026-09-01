import React from 'react';
import { useTranslation } from 'react-i18next';
import { Volume2, Camera, ChevronRight, CheckCircle2, WifiOff, ShieldCheck } from 'lucide-react';
import { LanguageCode } from '../types';
import { LANGUAGES } from '../data/translations';

interface LanguageStepProps {
  onProceed: () => void;
  onPlayVoice: (text: string) => void;
}

export const LanguageStep: React.FC<LanguageStepProps> = ({
  onProceed,
  onPlayVoice,
}) => {
  const { t, i18n } = useTranslation();
  const currentLang = i18n.language as LanguageCode;

  const handleSelectLanguage = (code: LanguageCode, audioText: string) => {
    i18n.changeLanguage(code);
    onPlayVoice(audioText);
  };

  return (
    <div className="max-w-xl mx-auto px-4 py-6 space-y-6">
      {/* Prominent S.P.O.T. Hero Splash Card */}
      <div className="bg-gradient-to-br from-[#1E3A2B] via-[#2D5A27] to-[#1E3A2B] text-white p-6 rounded-3xl shadow-xl border-4 border-[#3A7D44] relative overflow-hidden">
        <div className="absolute -right-8 -bottom-8 opacity-20 pointer-events-none text-9xl">
          🧅
        </div>
        <div className="relative z-10 space-y-3 text-center sm:text-left">
          <div className="inline-flex items-center gap-2 bg-[#0F281E] text-emerald-300 text-xs px-3 py-1 rounded-full font-black uppercase tracking-wider border border-[#81C784]/40 shadow-sm">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            <span>S.P.O.T. PWA • Offline ServiceWorker Active</span>
          </div>
          
          <div className="space-y-1">
            <h2 className="text-3xl sm:text-4xl font-black leading-tight tracking-tight text-white drop-shadow-md">
              S.P.O.T.
            </h2>
            <p className="text-emerald-200 text-xs uppercase font-extrabold tracking-widest">
              Smart Produce Optimization & Tracking
            </p>
          </div>

          <p className="text-emerald-100 text-sm font-semibold pt-1 border-t border-emerald-500/30">
            {t('selectLangSubtitle')}
          </p>
        </div>
      </div>

      {/* Grid of Oversized Language Selection Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {LANGUAGES.map((item) => {
          const isSelected = currentLang === item.code;
          return (
            <div
              key={item.code}
              onClick={() => handleSelectLanguage(item.code, item.audioText)}
              className={`cursor-pointer p-5 rounded-3xl border-4 transition-all duration-200 flex items-center justify-between shadow-md relative overflow-hidden select-none active:scale-95 ${
                isSelected
                  ? 'bg-white border-[#2D5A27] ring-4 ring-[#81C784]/50 shadow-xl'
                  : 'bg-white/80 hover:bg-white border-stone-200 hover:border-[#3A7D44]'
              }`}
            >
              <div className="flex items-center gap-4">
                <span className="text-4xl bg-emerald-100/60 p-2 rounded-2xl border border-emerald-200">
                  {item.flag}
                </span>
                <div>
                  <h3 className="text-xl font-extrabold text-[#0F281E] tracking-wide">
                    {item.nativeName}
                  </h3>
                  <p className="text-xs font-semibold text-stone-500">{item.name}</p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleSelectLanguage(item.code, item.audioText);
                  }}
                  className="p-3 bg-emerald-50 hover:bg-emerald-100 active:scale-90 text-[#2D5A27] rounded-2xl border border-emerald-200"
                  title={t('listenInstruction')}
                >
                  <Volume2 className="w-6 h-6 text-[#2D5A27]" />
                </button>

                {isSelected ? (
                  <CheckCircle2 className="w-8 h-8 text-[#2D5A27] fill-[#81C784]" />
                ) : (
                  <div className="w-7 h-7 rounded-full border-2 border-stone-300" />
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Giant CTA Button */}
      <div className="pt-2">
        <button
          onClick={onProceed}
          className="w-full btn-oversized bg-[#2D5A27] hover:bg-[#1E3A2B] text-white py-5 px-6 rounded-3xl border-4 border-[#81C784] shadow-2xl animate-pulse-ring flex items-center justify-between text-xl font-extrabold tracking-wide"
        >
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-emerald-600 rounded-2xl flex items-center justify-center border-2 border-white/40">
              <Camera className="w-7 h-7 text-white" />
            </div>
            <span>{t('startScanBtn')}</span>
          </div>
          <ChevronRight className="w-8 h-8 text-emerald-200" />
        </button>
      </div>

      {/* Offline Agricultural Guarantee Card */}
      <div className="bg-[#1E3A2B] text-white p-4 rounded-2xl border-2 border-[#3A7D44] flex items-center justify-between text-xs font-bold shadow-md">
        <div className="flex items-center gap-2.5">
          <WifiOff className="w-5 h-5 text-amber-300" />
          <div>
            <p className="font-extrabold text-emerald-200">S.P.O.T. Field Guarantee</p>
            <p className="text-[11px] text-stone-300">Works 100% offline in remote farms without signal</p>
          </div>
        </div>
        <span className="bg-[#81C784] text-[#0F281E] px-2.5 py-1 rounded-lg font-black uppercase text-[10px]">
          Verified
        </span>
      </div>
    </div>
  );
};
