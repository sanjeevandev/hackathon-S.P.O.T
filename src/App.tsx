import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Header } from './components/Header';
import { HomeStep } from './components/HomeStep';
import { NewInspectionStep } from './components/NewInspectionStep';
import { CaptureStep } from './components/CaptureStep';
import { AnalyzingStep } from './components/AnalyzingStep';
import { ResultStep } from './components/ResultStep';
import { EvidenceStep } from './components/EvidenceStep';
import { ReportStep } from './components/ReportStep';
import { HistoryStep } from './components/HistoryStep';
import { VerifyStep } from './components/VerifyStep';
import { AdminStep } from './components/AdminStep';
import { PresenterToolbar } from './components/PresenterToolbar';
import { AppRoute, CanonicalInspectionResult, NewInspectionMeta } from './types';
import { getCanonicalResult } from './api/inspections';

export function App() {
  const { i18n } = useTranslation();
  const [currentRoute, setCurrentRoute] = useState<AppRoute>('home');

  const [inspectionMeta, setInspectionMeta] = useState<NewInspectionMeta | null>(null);
  const [capturedFile, setCapturedFile] = useState<File | null>(null);
  const [canonicalResult, setCanonicalResult] = useState<CanonicalInspectionResult | null>(null);
  const [activeInspectionId, setActiveInspectionId] = useState<string | null>(null);

  const [isOffline, setIsOffline] = useState<boolean>(!navigator.onLine);
  const [deferredPrompt, setDeferredPrompt] = useState<any>(null);
  const [verifyBatchId, setVerifyBatchId] = useState<string | null>(null);
  const [judgeDemoMode, setJudgeDemoMode] = useState<boolean>(false);
  const [isPresenterToolbarOpen, setIsPresenterToolbarOpen] = useState<boolean>(false);
  const [isServerAiMode, setIsServerAiMode] = useState<boolean>(false);

  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const batchParam = urlParams.get('batch_id');
    if (window.location.pathname.includes('/verify') || batchParam) {
      setVerifyBatchId(batchParam || 'BATCH-MH-2026-891');
    } else if (window.location.pathname.includes('/admin')) {
      setCurrentRoute('admin');
    }

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.shiftKey && (e.key === 'P' || e.key === 'p')) {
        e.preventDefault();
        setIsPresenterToolbarOpen((prev) => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);

    const handleOnline = () => setIsOffline(false);
    const handleOffline = () => setIsOffline(true);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    const handleBeforeInstallPrompt = (e: Event) => {
      e.preventDefault();
      setDeferredPrompt(e);
    };

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    };
  }, []);

  const handlePlayVoice = (text: string) => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.95;
      utterance.pitch = 1.0;
      const langMap: Record<string, string> = { en: 'en-US', hi: 'hi-IN', mr: 'mr-IN', ta: 'ta-IN' };
      utterance.lang = langMap[i18n.language] || 'en-US';
      window.speechSynthesis.speak(utterance);
    }
  };

  const handleStartNewInspection = () => {
    setCanonicalResult(null);
    setCapturedFile(null);
    setInspectionMeta(null);
    setActiveInspectionId(null);
    setCurrentRoute('new_inspection');
  };

  const handleSelectHistoryInspection = async (inspectionId: string) => {
    try {
      setActiveInspectionId(inspectionId);
      const res = await getCanonicalResult(inspectionId);
      setCanonicalResult(res);
      setCurrentRoute('result');
    } catch (err: any) {
      alert(`Failed to load stored inspection result: ${err.message}`);
    }
  };

  if (verifyBatchId) {
    return (
      <div className="min-h-screen bg-[#F7F5F0] text-[#0F281E] font-sans">
        <VerifyStep
          batchId={verifyBatchId}
          onBackToApp={() => {
            setVerifyBatchId(null);
            window.history.pushState({}, '', '/');
          }}
        />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F7F5F0] text-[#0F281E] flex flex-col font-sans pb-12">
      <Header
        currentStep={currentRoute as any}
        onSelectStep={(step) => setCurrentRoute(step as AppRoute)}
        onPlayVoice={handlePlayVoice}
        isOffline={isOffline}
        canInstallPwa={Boolean(deferredPrompt)}
        onInstallPwa={() => deferredPrompt?.prompt()}
        judgeDemoMode={judgeDemoMode}
        onToggleJudgeDemoMode={() => {
          setJudgeDemoMode(!judgeDemoMode);
          if (!judgeDemoMode) handleStartNewInspection();
        }}
        onTogglePresenterToolbar={() => setIsPresenterToolbarOpen(!isPresenterToolbarOpen)}
      />

      <main className="flex-1">
        {currentRoute === 'home' && (
          <HomeStep
            onNavigate={setCurrentRoute}
            onStartNewInspection={handleStartNewInspection}
          />
        )}

        {currentRoute === 'new_inspection' && (
          <NewInspectionStep
            onBack={() => setCurrentRoute('home')}
            onProceed={(meta) => {
              setInspectionMeta(meta);
              setCurrentRoute('capture');
            }}
          />
        )}

        {currentRoute === 'capture' && inspectionMeta && (
          <CaptureStep
            meta={inspectionMeta}
            onBack={() => setCurrentRoute('new_inspection')}
            onImageSelected={(file) => {
              setCapturedFile(file);
              setCurrentRoute('analyzing');
            }}
          />
        )}

        {currentRoute === 'analyzing' && inspectionMeta && capturedFile && (
          <AnalyzingStep
            meta={inspectionMeta}
            file={capturedFile}
            onSuccess={(result) => {
              setCanonicalResult(result);
              setActiveInspectionId(result.inspection_id);
              setCurrentRoute('result');
            }}
            onError={(err) => {
              alert(`Inspection pipeline error: ${err}`);
              setCurrentRoute('home');
            }}
          />
        )}

        {currentRoute === 'result' && canonicalResult && (
          <ResultStep
            result={canonicalResult}
            onNavigate={setCurrentRoute}
            onNewInspection={handleStartNewInspection}
          />
        )}

        {currentRoute === 'evidence' && canonicalResult && (
          <EvidenceStep
            result={canonicalResult}
            onBack={() => setCurrentRoute('result')}
          />
        )}

        {currentRoute === 'report' && (activeInspectionId || canonicalResult?.inspection_id) && (
          <ReportStep
            inspectionId={activeInspectionId || canonicalResult!.inspection_id}
            onBack={() => setCurrentRoute('result')}
          />
        )}

        {currentRoute === 'history' && (
          <HistoryStep
            onSelectInspection={handleSelectHistoryInspection}
            onBack={() => setCurrentRoute('home')}
          />
        )}

        {currentRoute === 'admin' && (
          <AdminStep
            onBackToApp={() => setCurrentRoute('home')}
            onPlayVoice={handlePlayVoice}
          />
        )}
      </main>

      <footer className="mt-auto py-4 text-center text-xs text-stone-500 font-bold border-t border-stone-200">
        <p>S.P.O.T. • Smart Produce Optimization & Tracking PWA</p>
        <p className="text-[10px] text-stone-400 mt-0.5">SIH 2026 AI Onion Quality Grading System • Digital Quality Inspection Report Engine</p>
      </footer>

      <PresenterToolbar
        isVisible={isPresenterToolbarOpen}
        onClose={() => setIsPresenterToolbarOpen(false)}
        onResetDemo={() => handleStartNewInspection()}
        isServerAiMode={isServerAiMode}
        onToggleAiMode={() => setIsServerAiMode(!isServerAiMode)}
        onSimulateHardware={() => {
          handlePlayVoice('Simulated scale weight sync active.');
        }}
      />
    </div>
  );
}

export default App;
