import React, { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { Mic, MicOff, X, Sparkles, AlertCircle, Camera, History, Home, Upload } from 'lucide-react';
import { AppRoute } from '../types';

interface VoiceCommandModalProps {
  isOpen: boolean;
  onClose: () => void;
  onNavigate: (route: AppRoute) => void;
  onStartNewInspection: () => void;
  onPlayVoice?: (text: string) => void;
}

export const VoiceCommandModal: React.FC<VoiceCommandModalProps> = ({
  isOpen,
  onClose,
  onNavigate,
  onStartNewInspection,
  onPlayVoice,
}) => {
  const { i18n } = useTranslation();
  const [isListening, setIsListening] = useState<boolean>(false);
  const [transcript, setTranscript] = useState<string>('');
  const [feedbackMessage, setFeedbackMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSupported, setIsSupported] = useState<boolean>(true);

  const recognitionRef = useRef<any>(null);
  const activeLang = i18n.language ? i18n.language.substring(0, 2) : 'en';

  useEffect(() => {
    if (!isOpen) {
      stopListening();
      setTranscript('');
      setFeedbackMessage(null);
      setErrorMessage(null);
      return;
    }

    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setIsSupported(false);
      setErrorMessage(
        'Voice speech recognition is not supported in this browser environment. Voice recognition is available in Google Chrome, Microsoft Edge, Safari, and Android Chromium WebViews.'
      );
      return;
    }

    setIsSupported(true);
    startListening();

    return () => {
      stopListening();
    };
  }, [isOpen, activeLang]);

  const startListening = () => {
    stopListening();
    setErrorMessage(null);
    setFeedbackMessage(null);
    setTranscript('');

    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setIsSupported(false);
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.maxAlternatives = 1;

      const langMap: Record<string, string> = {
        en: 'en-US',
        hi: 'hi-IN',
        mr: 'mr-IN',
        ta: 'ta-IN',
      };
      recognition.lang = langMap[activeLang] || 'en-US';

      recognition.onstart = () => {
        setIsListening(true);
        setErrorMessage(null);
      };

      recognition.onresult = (event: any) => {
        let current = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
          current += event.results[i][0].transcript;
        }
        setTranscript(current);

        if (event.results[0] && event.results[0].isFinal) {
          handleProcessCommand(current.trim().toLowerCase());
        }
      };

      recognition.onerror = (event: any) => {
        setIsListening(false);
        console.warn('[VoiceCommand] Recognition error:', event.error);
        if (event.error === 'not-allowed' || event.error === 'permission-denied') {
          setErrorMessage('Microphone access was denied. Please allow microphone permissions in browser settings.');
        } else if (event.error === 'no-speech') {
          setErrorMessage('No speech was detected. Tap the mic to try speaking again.');
        } else if (event.error === 'audio-capture') {
          setErrorMessage('No microphone device found on this system.');
        } else if (event.error === 'network') {
          setErrorMessage('Voice recognition service network error. Please try again.');
        } else {
          setErrorMessage(`Voice capture error: ${event.error}. Tap mic to retry.`);
        }
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognitionRef.current = recognition;
      recognition.start();
    } catch (err: any) {
      console.warn('[VoiceCommand] Start failed:', err);
      setIsListening(false);
      setErrorMessage('Could not initialize microphone. Please check permissions.');
    }
  };

  const stopListening = () => {
    if (recognitionRef.current) {
      try {
        recognitionRef.current.abort();
      } catch (_) {}
      recognitionRef.current = null;
    }
    setIsListening(false);
  };

  const handleProcessCommand = (spoken: string) => {
    stopListening();
    const clean = spoken.toLowerCase().replace(/[.,/#!$%^&*;:{}=\-_`~()]/g, '');

    // 1. Scan / New Inspection
    if (
      clean.includes('scan') ||
      clean.includes('start') ||
      clean.includes('new inspection') ||
      clean.includes('camera') ||
      clean.includes('inspect') ||
      clean.includes('तपासणी') ||
      clean.includes('स्कॅन') ||
      clean.includes('जांच')
    ) {
      setFeedbackMessage('Starting New Inspection...');
      if (onPlayVoice) onPlayVoice('Starting New Inspection');
      setTimeout(() => {
        onClose();
        onStartNewInspection();
      }, 500);
      return;
    }

    // 2. History
    if (
      clean.includes('history') ||
      clean.includes('record') ||
      clean.includes('past') ||
      clean.includes('logs') ||
      clean.includes('इतिहास') ||
      clean.includes('मागील') ||
      clean.includes('पिछला')
    ) {
      setFeedbackMessage('Opening Inspection History...');
      if (onPlayVoice) onPlayVoice('Opening History');
      setTimeout(() => {
        onClose();
        onNavigate('history');
      }, 500);
      return;
    }

    // 3. Home
    if (
      clean.includes('home') ||
      clean.includes('main') ||
      clean.includes('dashboard') ||
      clean.includes('घर') ||
      clean.includes('मुख्य')
    ) {
      setFeedbackMessage('Returning to Home...');
      if (onPlayVoice) onPlayVoice('Navigating to Home');
      setTimeout(() => {
        onClose();
        onNavigate('home');
      }, 500);
      return;
    }

    // 4. Upload
    if (
      clean.includes('upload') ||
      clean.includes('file') ||
      clean.includes('photo') ||
      clean.includes('अपलोड')
    ) {
      setFeedbackMessage('Opening Scan Upload...');
      if (onPlayVoice) onPlayVoice('Opening Upload');
      setTimeout(() => {
        onClose();
        onStartNewInspection();
      }, 500);
      return;
    }

    // 5. Assistant / Help
    if (
      clean.includes('assistant') ||
      clean.includes('help') ||
      clean.includes('faq') ||
      clean.includes('guide') ||
      clean.includes('मदत') ||
      clean.includes('सहायक')
    ) {
      setFeedbackMessage('Opening AI Assistant...');
      if (onPlayVoice) onPlayVoice('Opening Assistant');
      setTimeout(() => {
        onClose();
        onNavigate('assistant');
      }, 500);
      return;
    }

    // 6. Admin / Officer
    if (
      clean.includes('admin') ||
      clean.includes('officer') ||
      clean.includes('supervisor') ||
      clean.includes('अधिकारी')
    ) {
      setFeedbackMessage('Opening Officer Portal...');
      if (onPlayVoice) onPlayVoice('Opening Officer Portal');
      setTimeout(() => {
        onClose();
        onNavigate('admin');
      }, 500);
      return;
    }

    // Unrecognized command
    setErrorMessage(`Command "${spoken}" not recognized. Try saying "Scan", "History", "Home", or "Upload".`);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs animate-in fade-in duration-150 font-sans">
      <div className="bg-[#163A2D] text-white w-full max-w-sm rounded-3xl p-6 shadow-2xl border border-white/20 space-y-5 relative">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-2 rounded-full bg-white/10 hover:bg-white/20 text-white/80 hover:text-white transition-colors cursor-pointer"
          aria-label="Close Voice Assistant"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Header */}
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-xl bg-[#E51E3A] flex items-center justify-center shadow-xs">
            <Mic className="w-4 h-4 text-white" />
          </div>
          <div>
            <h3 className="text-base font-black tracking-tight text-white">Voice Command</h3>
            <p className="text-[10px] text-white/70 font-bold uppercase tracking-wider">
              {isListening ? 'Listening...' : isSupported ? 'Ready for command' : 'Voice status'}
            </p>
          </div>
        </div>

        {/* Central Pulsing Microphone Indicator */}
        <div className="flex flex-col items-center justify-center py-3 space-y-3">
          <button
            onClick={isListening ? stopListening : startListening}
            className={`w-20 h-20 rounded-full flex items-center justify-center transition-all duration-300 active:scale-95 cursor-pointer ${
              isListening
                ? 'bg-[#E51E3A] ring-8 ring-[#E51E3A]/40 animate-pulse shadow-[0_0_25px_rgba(229,30,58,0.6)]'
                : 'bg-white/15 hover:bg-white/25 border-2 border-white/30 text-white'
            }`}
            aria-label={isListening ? 'Stop Listening' : 'Start Listening'}
          >
            {isListening ? (
              <Mic className="w-10 h-10 text-white animate-bounce" />
            ) : (
              <MicOff className="w-9 h-9 text-white/70" />
            )}
          </button>

          <div className="text-center">
            {isListening ? (
              <div className="space-y-1">
                <span className="text-sm font-black text-emerald-300 block animate-pulse">
                  Listening...
                </span>
                <span className="text-[11px] text-white/80 block">
                  Speak clearly into your microphone
                </span>
              </div>
            ) : (
              <span className="text-xs font-bold text-white/80 block">
                {isSupported ? 'Tap microphone to speak' : 'Voice command unavailable'}
              </span>
            )}
          </div>
        </div>

        {/* Real-time Spoken Transcript or Feedback */}
        {transcript && (
          <div className="bg-black/30 p-3 rounded-2xl border border-white/15 text-center">
            <span className="text-[10px] font-bold text-white/60 block uppercase tracking-wider">
              Detected Speech:
            </span>
            <p className="text-xs font-black text-white mt-0.5 italic">
              "{transcript}"
            </p>
          </div>
        )}

        {feedbackMessage && (
          <div className="bg-emerald-500/20 p-3 rounded-2xl border border-emerald-400/40 text-center flex items-center justify-center gap-2">
            <Sparkles className="w-4 h-4 text-emerald-300" />
            <span className="text-xs font-black text-emerald-200">{feedbackMessage}</span>
          </div>
        )}

        {errorMessage && (
          <div className="bg-[#E51E3A]/20 p-3 rounded-2xl border border-[#E51E3A]/40 text-left flex items-start gap-2 text-[11px] text-rose-200 leading-snug font-medium">
            <AlertCircle className="w-4 h-4 text-[#E51E3A] shrink-0 mt-0.5" />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Quick Tap Command Fallbacks */}
        <div className="space-y-2 pt-1 border-t border-white/10">
          <span className="text-[10px] font-black uppercase tracking-wider text-white/60 block">
            Available Voice Commands:
          </span>
          <div className="grid grid-cols-2 gap-2">
            <button
              onClick={() => handleProcessCommand('scan')}
              className="p-2 bg-white/10 hover:bg-white/20 active:scale-95 rounded-xl text-left flex items-center gap-2 transition-all cursor-pointer border border-white/10"
            >
              <Camera className="w-3.5 h-3.5 text-[#E51E3A]" />
              <span className="text-[11px] font-bold">"Scan"</span>
            </button>

            <button
              onClick={() => handleProcessCommand('history')}
              className="p-2 bg-white/10 hover:bg-white/20 active:scale-95 rounded-xl text-left flex items-center gap-2 transition-all cursor-pointer border border-white/10"
            >
              <History className="w-3.5 h-3.5 text-amber-300" />
              <span className="text-[11px] font-bold">"History"</span>
            </button>

            <button
              onClick={() => handleProcessCommand('home')}
              className="p-2 bg-white/10 hover:bg-white/20 active:scale-95 rounded-xl text-left flex items-center gap-2 transition-all cursor-pointer border border-white/10"
            >
              <Home className="w-3.5 h-3.5 text-emerald-400" />
              <span className="text-[11px] font-bold">"Home"</span>
            </button>

            <button
              onClick={() => handleProcessCommand('upload')}
              className="p-2 bg-white/10 hover:bg-white/20 active:scale-95 rounded-xl text-left flex items-center gap-2 transition-all cursor-pointer border border-white/10"
            >
              <Upload className="w-3.5 h-3.5 text-sky-300" />
              <span className="text-[11px] font-bold">"Upload"</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
