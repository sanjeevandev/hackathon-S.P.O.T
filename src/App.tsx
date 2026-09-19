import { useState, useEffect, lazy, Suspense } from 'react';
import { useTranslation } from 'react-i18next';
import { Header } from './components/Header';
import { BottomNav } from './components/BottomNav';
import { LandingPage } from './components/LandingPage';
import { HomeStep } from './components/HomeStep';
import { NewInspectionStep } from './components/NewInspectionStep';
import { CaptureStep } from './components/CaptureStep';
import { AnalyzingStep } from './components/AnalyzingStep';
import { ResultStep } from './components/ResultStep';
import { VoiceCommandModal } from './components/VoiceCommandModal';
import { PresenterToolbar } from './components/PresenterToolbar';
import { ErrorBoundary } from './components/ErrorBoundary';
import { App as CapacitorApp } from '@capacitor/app';
import { AppRoute, CanonicalInspectionResult, NewInspectionMeta } from './types';
import { getCanonicalResult } from './api/inspections';
import { Loader2 } from 'lucide-react';

// Lazy-loaded secondary & protected routes
const AdminStep = lazy(() => import('./components/AdminStep').then(m => ({ default: m.AdminStep })));
const AnnotationWorkstationStep = lazy(() => import('./components/AnnotationWorkstationStep').then(m => ({ default: m.AnnotationWorkstationStep })));
const AnalyticsStep = lazy(() => import('./components/AnalyticsStep').then(m => ({ default: m.AnalyticsStep })));
const AssistantStep = lazy(() => import('./components/AssistantStep').then(m => ({ default: m.AssistantStep })));
const HistoryStep = lazy(() => import('./components/HistoryStep').then(m => ({ default: m.HistoryStep })));
const ReportStep = lazy(() => import('./components/ReportStep').then(m => ({ default: m.ReportStep })));
const EvidenceStep = lazy(() => import('./components/EvidenceStep').then(m => ({ default: m.EvidenceStep })));
const VerifyStep = lazy(() => import('./components/VerifyStep').then(m => ({ default: m.VerifyStep })));

function RouteLoadingFallback() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[300px] p-8 text-center space-y-3 font-sans">
      <Loader2 className="w-8 h-8 text-[#163A2D] animate-spin" />
      <span className="text-xs font-bold text-[#163A2D]/70 uppercase tracking-wider">
        Loading...
      </span>
    </div>
  );
}

function isAnnotationRoute(): boolean {
  const path = window.location.pathname.toLowerCase();
  const hash = window.location.hash.toLowerCase();
  const search = window.location.search.toLowerCase();
  return (
    path.includes('/internal/annotation') ||
    hash.includes('internal-annotation') ||
    search.includes('annotation=true')
  );
}

function getInitialRoute(): AppRoute {
  if (isAnnotationRoute()) {
    return 'internal_annotation';
  }
  const search = window.location.search.toLowerCase();
  if (search.includes('verify=')) {
    return 'home';
  }
  // Mobile app always launches cleanly into the Landing Screen
  return 'landing';
}

export function App() {
  const { i18n } = useTranslation();
  const [currentRoute, setCurrentRoute] = useState<AppRoute>(getInitialRoute);
  const [inspectionMeta, setInspectionMeta] = useState<NewInspectionMeta | null>(null);
  const [capturedFile, setCapturedFile] = useState<File | null>(null);
  const [canonicalResult, setCanonicalResult] = useState<CanonicalInspectionResult | null>(null);
  const [activeInspectionId, setActiveInspectionId] = useState<string | null>(null);

  const [isOffline, setIsOffline] = useState<boolean>(!navigator.onLine);
  const [deferredPrompt, setDeferredPrompt] = useState<any>(null);
  const [verifyBatchId, setVerifyBatchId] = useState<string | null>(null);
  const [isPresenterToolbarOpen, setIsPresenterToolbarOpen] = useState<boolean>(false);
  const [isVoiceCommandOpen, setIsVoiceCommandOpen] = useState<boolean>(false);

  useEffect(() => {
    // On native app launch, immediately reset any stale WebView URL path to root
    try {
      window.history.replaceState({}, '', '/');
    } catch (_) {}

    const urlParams = new URLSearchParams(window.location.search);
    const batchParam = urlParams.get('batch_id') || urlParams.get('verify');
    if (batchParam) {
      setVerifyBatchId(batchParam);
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

    // Native Android Hardware Back Button Handling
    let backButtonHandle: any = null;
    CapacitorApp.addListener('backButton', () => {
      setCurrentRoute((prev) => {
        if (prev === 'landing') {
          CapacitorApp.exitApp();
          return 'landing';
        }
        if (prev === 'evidence' || prev === 'report') {
          return 'result';
        }
        if (prev === 'capture' || prev === 'analyzing') {
          return 'new_inspection';
        }
        if (prev === 'new_inspection' || prev === 'history' || prev === 'analytics' || prev === 'assistant' || prev === 'admin' || prev === 'result') {
          return 'home';
        }
        if (prev === 'home') {
          return 'landing';
        }
        return 'home';
      });
    }).then((handle) => {
      backButtonHandle = handle;
    }).catch(() => {
      // Ignore if not in native runtime
    });

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
      if (backButtonHandle) {
        backButtonHandle.remove();
      }
    };
  }, []);

  const navigateToRoute = (route: AppRoute) => {
    setCurrentRoute(route);
  };

  const handlePlayVoice = (text: string) => {
    if ('speechSynthesis' in window) {
      try {
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 0.95;
        utterance.pitch = 1.0;
        const currentLang = i18n.language ? i18n.language.substring(0, 2) : 'en';
        const langMap: Record<string, string> = { en: 'en-US', hi: 'hi-IN', mr: 'mr-IN', ta: 'ta-IN' };
        utterance.lang = langMap[currentLang] || 'en-US';
        window.speechSynthesis.speak(utterance);
      } catch (err) {
        console.warn('SpeechSynthesis error:', err);
      }
    }
  };

  const handleStartNewInspection = () => {
    setCanonicalResult(null);
    setCapturedFile(null);
    setInspectionMeta({
      batch_id: 'BATCH-MH-NASHIK-01',
      supplier: 'Nashik Farmers Producer Co.',
      procurement_center_id: 'APMC-NASHIK-CENTER-04',
      sampling_status: 'SAMPLE_ONLY',
    });
    setActiveInspectionId(null);
    navigateToRoute('new_inspection');
  };

  const handleSelectHistoryInspection = async (inspectionId: string) => {
    try {
      setActiveInspectionId(inspectionId);
      const res = await getCanonicalResult(inspectionId);
      setCanonicalResult(res);
      setCurrentRoute('result');
    } catch (err: any) {
      alert(`Failed to load stored inspection result: ${err.message || err}`);
    }
  };

  // Annotation route
  if (currentRoute === 'internal_annotation') {
    return (
      <ErrorBoundary componentName="Annotation Workstation">
        <Suspense fallback={<RouteLoadingFallback />}>
          <AnnotationWorkstationStep
            onBackToApp={() => navigateToRoute('home')}
          />
        </Suspense>
      </ErrorBoundary>
    );
  }

  // Verification Gate route
  if (verifyBatchId) {
    return (
      <div className="min-h-screen bg-[#F7F1E7] text-[#163A2D] font-sans">
        <ErrorBoundary componentName="Verification Gateway">
          <Suspense fallback={<RouteLoadingFallback />}>
            <VerifyStep
              batchId={verifyBatchId}
              onBackToApp={() => {
                setVerifyBatchId(null);
                window.history.pushState({}, '', '/');
              }}
            />
          </Suspense>
        </ErrorBoundary>
      </div>
    );
  }

  // 1. DEFAULT STARTUP VIEW: Standalone Mobile-First Landing Page
  if (currentRoute === 'landing') {
    return (
      <ErrorBoundary componentName="Landing Page">
        <LandingPage
          onStartInspection={handleStartNewInspection}
          onViewHistory={() => navigateToRoute('history')}
          onContinue={() => navigateToRoute('home')}
          onEnterDashboard={() => navigateToRoute('home')}
          isOffline={isOffline}
        />
      </ErrorBoundary>
    );
  }

  // 2. MAIN MOBILE APPLICATION SHELL
  return (
    <div className="min-h-screen bg-[#F7F1E7] text-[#163A2D] flex flex-col font-sans">
      {/* Mobile-First Centered Container (Max 430px for perfection across all phones) */}
      <div className="w-full max-w-md mx-auto min-h-screen bg-[#F7F1E7] flex flex-col shadow-xl relative border-x border-[#163A2D]/10">
        <Header
          currentStep={currentRoute}
          onSelectStep={(step) => navigateToRoute(step)}
          onPlayVoice={handlePlayVoice}
          onOpenVoiceCommand={() => setIsVoiceCommandOpen(true)}
          isOffline={isOffline}
          canInstallPwa={Boolean(deferredPrompt)}
          onInstallPwa={() => deferredPrompt?.prompt()}
          onTogglePresenterToolbar={() => setIsPresenterToolbarOpen(!isPresenterToolbarOpen)}
        />

        <main className="flex-1">
          <ErrorBoundary componentName="Application View">
            {currentRoute === 'home' && (
              <HomeStep
                onNavigate={navigateToRoute}
                onStartNewInspection={handleStartNewInspection}
              />
            )}

            {currentRoute === 'new_inspection' && (
              <NewInspectionStep
                onBack={() => navigateToRoute('home')}
                onProceed={(meta) => {
                  setInspectionMeta(meta);
                  setCurrentRoute('capture');
                }}
              />
            )}

            {currentRoute === 'capture' && (
              <CaptureStep
                meta={
                  inspectionMeta || {
                    batch_id: 'BATCH-MH-NASHIK-01',
                    supplier: 'APMC Lot Intake',
                    procurement_center_id: 'APMC-NASHIK-CENTER-04',
                    sampling_status: 'SAMPLE_ONLY',
                  }
                }
                onBack={() => navigateToRoute('home')}
                onImageSelected={(file) => {
                  setCapturedFile(file);
                  setCurrentRoute('analyzing');
                }}
              />
            )}

            {currentRoute === 'analyzing' && capturedFile && (
              <AnalyzingStep
                meta={
                  inspectionMeta || {
                    batch_id: 'BATCH-MH-NASHIK-01',
                    supplier: 'APMC Lot Intake',
                    procurement_center_id: 'APMC-NASHIK-CENTER-04',
                    sampling_status: 'SAMPLE_ONLY',
                  }
                }
                file={capturedFile}
                onSuccess={(result) => {
                  setCanonicalResult(result);
                  setActiveInspectionId(result.inspection_id);
                  setCurrentRoute('result');
                }}
                onError={() => {
                  navigateToRoute('home');
                }}
                onRetryScan={() => {
                  setCurrentRoute('capture');
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
              <Suspense fallback={<RouteLoadingFallback />}>
                <EvidenceStep
                  result={canonicalResult}
                  onBack={() => setCurrentRoute('result')}
                />
              </Suspense>
            )}

            {currentRoute === 'report' && (activeInspectionId || canonicalResult?.inspection_id) && (
              <Suspense fallback={<RouteLoadingFallback />}>
                <ReportStep
                  inspectionId={activeInspectionId || canonicalResult!.inspection_id}
                  onBack={() => setCurrentRoute('result')}
                />
              </Suspense>
            )}

            {currentRoute === 'history' && (
              <Suspense fallback={<RouteLoadingFallback />}>
                <HistoryStep
                  onSelectInspection={handleSelectHistoryInspection}
                  onBack={() => navigateToRoute('home')}
                />
              </Suspense>
            )}

            {currentRoute === 'analytics' && (
              <Suspense fallback={<RouteLoadingFallback />}>
                <AnalyticsStep
                  onBack={() => navigateToRoute('home')}
                  onStartNewInspection={handleStartNewInspection}
                />
              </Suspense>
            )}

            {currentRoute === 'assistant' && (
              <Suspense fallback={<RouteLoadingFallback />}>
                <AssistantStep
                  onBack={() => navigateToRoute('home')}
                />
              </Suspense>
            )}

            {currentRoute === 'admin' && (
              <Suspense fallback={<RouteLoadingFallback />}>
                <AdminStep
                  onBackToApp={() => navigateToRoute('home')}
                  onPlayVoice={handlePlayVoice}
                />
              </Suspense>
            )}
          </ErrorBoundary>
        </main>

        {/* Mobile Bottom Navigation */}
        <BottomNav
          currentRoute={currentRoute}
          onNavigate={navigateToRoute}
          onStartScan={handleStartNewInspection}
        />

        <VoiceCommandModal
          isOpen={isVoiceCommandOpen}
          onClose={() => setIsVoiceCommandOpen(false)}
          onNavigate={navigateToRoute}
          onStartNewInspection={handleStartNewInspection}
          onPlayVoice={handlePlayVoice}
        />

        <PresenterToolbar
          isVisible={isPresenterToolbarOpen}
          onClose={() => setIsPresenterToolbarOpen(false)}
          onResetDemo={() => handleStartNewInspection()}
        />
      </div>
    </div>
  );
}

export default App;
