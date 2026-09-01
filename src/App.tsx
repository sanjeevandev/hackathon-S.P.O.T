import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Header } from './components/Header';
import { LanguageStep } from './components/LanguageStep';
import { CameraStep } from './components/CameraStep';
import { ResultsStep } from './components/ResultsStep';
import { HistoryStep } from './components/HistoryStep';
import { VerifyStep } from './components/VerifyStep';
import { AdminStep } from './components/AdminStep';
import { PresenterToolbar } from './components/PresenterToolbar';
import { AppStep, ScanResult } from './types';
import { JUDGE_DEMO_SAMPLES } from './data/judgeSamples';

export function App() {
  const { i18n } = useTranslation();
  const [currentStep, setCurrentStep] = useState<AppStep>('language');
  const [scanResult, setScanResult] = useState<ScanResult | null>(null);
  const [isOffline, setIsOffline] = useState<boolean>(!navigator.onLine);
  const [deferredPrompt, setDeferredPrompt] = useState<any>(null);
  const [verifyBatchId, setVerifyBatchId] = useState<string | null>(null);
  const [judgeDemoMode, setJudgeDemoMode] = useState<boolean>(false);
  const [isPresenterToolbarOpen, setIsPresenterToolbarOpen] = useState<boolean>(false);
  const [isServerAiMode, setIsServerAiMode] = useState<boolean>(false);

  useEffect(() => {
    // Check if opening via QR Code verification link (/verify?batch_id=...) or /admin
    const urlParams = new URLSearchParams(window.location.search);
    const batchParam = urlParams.get('batch_id');
    if (window.location.pathname.includes('/verify') || batchParam) {
      setVerifyBatchId(batchParam || 'BATCH-MH-2026-891');
    } else if (window.location.pathname.includes('/admin')) {
      setCurrentStep('admin');
    }

    // Global Shift + P hotkey listener for Presenter Floating Toolbar
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

      const langMap: Record<string, string> = {
        en: 'en-US',
        hi: 'hi-IN',
        mr: 'mr-IN',
        ta: 'ta-IN',
      };
      utterance.lang = langMap[i18n.language] || 'en-US';
      window.speechSynthesis.speak(utterance);
    }
  };

  const handleCaptureResult = (result: ScanResult) => {
    setScanResult(result);
    setCurrentStep('results');
  };

  const handleSelectHistoryReport = (result: ScanResult) => {
    setScanResult(result);
    setCurrentStep('results');
  };

  const handleInstallPwa = () => {
    if (deferredPrompt) {
      deferredPrompt.prompt();
      deferredPrompt.userChoice.then((choiceResult: any) => {
        if (choiceResult.outcome === 'accepted') {
          console.log('User accepted S.P.O.T. PWA installation');
        }
        setDeferredPrompt(null);
      });
    } else {
      alert('To install S.P.O.T., tap "Add to Home Screen" in your browser menu!');
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
        currentStep={currentStep}
        onSelectStep={setCurrentStep}
        onPlayVoice={handlePlayVoice}
        isOffline={isOffline}
        canInstallPwa={Boolean(deferredPrompt)}
        onInstallPwa={handleInstallPwa}
        judgeDemoMode={judgeDemoMode}
        onToggleJudgeDemoMode={() => {
          setJudgeDemoMode(!judgeDemoMode);
          if (!judgeDemoMode) {
            setCurrentStep('camera');
            handlePlayVoice('Judge Evaluation Mode Activated. Choose a pre-loaded batch sample.');
          }
        }}
        onTogglePresenterToolbar={() => setIsPresenterToolbarOpen(!isPresenterToolbarOpen)}
      />

      <main className="flex-1">
        {currentStep === 'language' && (
          <LanguageStep
            onProceed={() => setCurrentStep('camera')}
            onPlayVoice={handlePlayVoice}
          />
        )}

        {currentStep === 'camera' && (
          <CameraStep
            onCapture={handleCaptureResult}
            onBack={() => setCurrentStep('language')}
            onPlayVoice={handlePlayVoice}
            judgeDemoMode={judgeDemoMode}
          />
        )}

        {currentStep === 'results' && (
          <ResultsStep
            result={scanResult}
            onResetScan={() => setCurrentStep('camera')}
            onPlayVoice={handlePlayVoice}
          />
        )}

        {currentStep === 'history' && (
          <HistoryStep
            onSelectReport={handleSelectHistoryReport}
            onPlayVoice={handlePlayVoice}
          />
        )}

        {currentStep === 'admin' && (
          <AdminStep
            onBackToApp={() => setCurrentStep('camera')}
            onPlayVoice={handlePlayVoice}
          />
        )}
      </main>

      <footer className="mt-auto py-4 text-center text-xs text-stone-500 font-bold border-t border-stone-200">
        <p>S.P.O.T. • Smart Produce Optimization & Tracking PWA</p>
        <p className="text-[10px] text-stone-400 mt-0.5">SIH 2026 AI Onion Quality Grading System • Offline ServiceWorker</p>
      </footer>

      {/* Presenter Floating Toolbar Modal (Triggered via Shift + P or 3s Logo Hold) */}
      <PresenterToolbar
        isVisible={isPresenterToolbarOpen}
        onClose={() => setIsPresenterToolbarOpen(false)}
        onResetDemo={() => {
          setScanResult(null);
          i18n.changeLanguage('hi');
          setCurrentStep('language');
          setJudgeDemoMode(false);
        }}
        isServerAiMode={isServerAiMode}
        onToggleAiMode={() => setIsServerAiMode(!isServerAiMode)}
        onSimulateHardware={() => {
          const sampleResult = JUDGE_DEMO_SAMPLES[0].result;
          const simulatedResult: ScanResult = {
            ...sampleResult,
            weightDistribution: {
              total_batch_weight_kg: 25.4,
              grade_a_weight_kg: 19.9,
              grade_urs_weight_kg: 3.8,
              rejected_weight_kg: 1.7,
              grade_a_weight_percentage: 78.3,
              grade_urs_weight_percentage: 15.0,
              rejected_weight_percentage: 6.7,
            }
          };
          setScanResult(simulatedResult);
          setCurrentStep('results');
          handlePlayVoice('Simulated scale weight 25.4 kg captured. Generating receipt print.');
        }}
      />
    </div>
  );
}

export default App;
