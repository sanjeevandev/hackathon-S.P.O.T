import React from 'react';
import { useTranslation } from 'react-i18next';
import { Home, Camera, History, Bot } from 'lucide-react';
import { AppRoute } from '../types';

interface BottomNavProps {
  currentRoute: AppRoute;
  onNavigate: (route: AppRoute) => void;
  onStartScan: () => void;
}

export const BottomNav: React.FC<BottomNavProps> = ({
  currentRoute,
  onNavigate,
  onStartScan,
}) => {
  const { t } = useTranslation();
  const isScanFlow = ['new_inspection', 'capture', 'analyzing', 'result', 'evidence', 'report'].includes(currentRoute);

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-40 bg-white/95 backdrop-blur-md border-t border-[#163A2D]/10 shadow-[0_-4px_20px_rgba(22,58,45,0.06)] font-sans">
      <div className="max-w-md mx-auto px-6 py-2 flex items-center justify-between relative h-16">
        {/* 1. Home */}
        <button
          onClick={() => onNavigate('home')}
          aria-label={t('home')}
          className={`flex flex-col items-center justify-center min-w-[56px] min-h-[44px] gap-0.5 rounded-xl transition-all ${
            currentRoute === 'home'
              ? 'text-[#E51E3A] font-black'
              : 'text-[#163A2D]/60 hover:text-[#163A2D] font-semibold'
          }`}
        >
          <Home className="w-5 h-5" />
          <span className="text-[10px]">{t('home')}</span>
        </button>

        {/* 2. Scan (Elevated Center CTA) */}
        <div className="relative -top-3 flex flex-col items-center">
          <button
            onClick={onStartScan}
            aria-label={t('scan')}
            className={`w-14 h-14 rounded-full flex items-center justify-center text-white shadow-lg transition-all transform active:scale-95 ${
              isScanFlow
                ? 'bg-[#163A2D] ring-4 ring-[#163A2D]/20 scale-105'
                : 'bg-[#E51E3A] hover:bg-[#c91530] ring-4 ring-[#E51E3A]/25 hover:scale-105'
            }`}
          >
            <Camera className="w-6 h-6" />
          </button>
          <span className="text-[9px] font-black text-[#163A2D] mt-0.5 uppercase tracking-wide">
            {t('scan')}
          </span>
        </div>

        {/* 3. History */}
        <button
          onClick={() => onNavigate('history')}
          aria-label={t('history')}
          className={`flex flex-col items-center justify-center min-w-[56px] min-h-[44px] gap-0.5 rounded-xl transition-all ${
            currentRoute === 'history'
              ? 'text-[#E51E3A] font-black'
              : 'text-[#163A2D]/60 hover:text-[#163A2D] font-semibold'
          }`}
        >
          <History className="w-5 h-5" />
          <span className="text-[10px]">{t('history')}</span>
        </button>

        {/* 4. Assistant */}
        <button
          onClick={() => onNavigate('assistant')}
          aria-label={t('assistant')}
          className={`flex flex-col items-center justify-center min-w-[56px] min-h-[44px] gap-0.5 rounded-xl transition-all ${
            currentRoute === 'assistant'
              ? 'text-[#E51E3A] font-black'
              : 'text-[#163A2D]/60 hover:text-[#163A2D] font-semibold'
          }`}
        >
          <Bot className="w-5 h-5" />
          <span className="text-[10px]">{t('assistant')}</span>
        </button>
      </div>
    </nav>
  );
};
