import React, { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { ArrowLeft, Bot, Sparkles, HelpCircle, Mic, MicOff, Volume2, VolumeX } from 'lucide-react';

interface AssistantStepProps {
  onBack: () => void;
}

interface QAItem {
  q: { en: string; hi: string; mr: string; ta: string };
  a: { en: string; hi: string; mr: string; ta: string };
}

const FAQ_KNOWLEDGE_BASE: QAItem[] = [
  {
    q: {
      en: 'What does Grade-A mean?',
      hi: 'Grade-A का क्या मतलब है?',
      mr: 'Grade-A चा अर्थ काय आहे?',
      ta: 'Grade-A என்பதன் பொருள் என்ன?'
    },
    a: {
      en: 'Grade-A denotes premium export quality onions with firm, dry outer skin and zero rot or sprouting. Suitable for long-term storage.',
      hi: 'Grade-A का मतलब है प्रीमियम गुणवत्ता वाला प्याज जिसमें कोई सड़न या अंकुरण नहीं है और छिलका सूखा है। यह लंबे भंडारण के लिए उत्तम है।',
      mr: 'Grade-A म्हणजे उत्कृष्ट गुणवत्तेचा कांदा ज्यामध्ये कोणतीही नासधूस किंवा मोड आलेले नसतात. दीर्घकालीन साठवणुकीसाठी योग्य.',
      ta: 'Grade-A என்பது உறுதியான, உலர்ந்த தோல் கொண்ட பிரீமியம் வெங்காயத்தைக் குறிக்கிறது. நீண்ட கால சேமிப்பிற்கு ஏற்றது.'
    }
  },
  {
    q: {
      en: 'What is Grade-URS in APMC?',
      hi: 'APMC में Grade-URS क्या है?',
      mr: 'APMC मध्ये Grade-URS काय आहे?',
      ta: 'APMC-ல் Grade-URS என்றால் என்ன?'
    },
    a: {
      en: 'Grade-URS (Under Relaxed Specifications) meets government procurement standards but has minor cosmetic flaws. Recommended to be sold within 20 days.',
      hi: 'Grade-URS सरकारी खरीद मानकों को पूरा करता है लेकिन इसमें मामूली खामियां हो सकती हैं। इसे 20 दिनों के भीतर स्थानीय मंडी में बेचने की सलाह दी जाती है।',
      mr: 'Grade-URS शासकीय खरेदी निकष पूर्ण करतो परंतु त्यात किरकोळ दोष असू शकतात. 20 दिवसांत स्थानिक बाजारात विकण्याची शिफारस केली जाते.',
      ta: 'Grade-URS என்பது அரசு கொள்முதல் தரநிலைகளை பூர்த்தி செய்யும் வெங்காயம். 20 நாட்களுக்குள் விற்க பரிந்துரைக்கப்படுகிறது.'
    }
  },
  {
    q: {
      en: 'Why was this onion classified as Defective?',
      hi: 'यह प्याज दोषयुक्त क्यों वर्गीकृत किया गया?',
      mr: 'हा कांदा दोषयुक्त का ठरवला गेला?',
      ta: 'இந்த வெங்காயம் குறைபாடுடையதாக ஏன் வகைப்படுத்தப்பட்டது?'
    },
    a: {
      en: 'Defective classification occurs when the YOLO26n-cls surface model detects visible defect characteristics on the onion exterior. As a binary classifier, it outputs HEALTHY or DEFECTIVE based on the overall image — it does not independently identify specific defect types like rot or sprouting.',
      hi: 'दोषयुक्त वर्गीकरण तब होता है जब YOLO26 मॉडल सतह पर दोष की विशेषताएं पहचानता है। यह एक बाइनरी क्लासिफायर है जो केवल HEALTHY या DEFECTIVE का निर्णय देता है।',
      mr: 'YOLO26 मॉडेलला पृष्ठभागावर दोषाची चिन्हे आढळल्यास दोषयुक्त ठरवले जाते. हे एक बायनरी क्लासिफायर आहे जे फक्त HEALTHY किंवा DEFECTIVE सांगते.',
      ta: 'YOLO26 மாதிரி வெளிப்புற குறைபாடுகளை கண்டறிந்தால் குறைபாடுடையதாக வகைப்படுத்தப்படும். இது ஒரு binary classifier ஆகும்.'
    }
  },
  {
    q: {
      en: 'Does S.P.O.T. inspect inside the onion?',
      hi: 'क्या S.P.O.T. प्याज के अंदरूनी भाग की जांच करता है?',
      mr: 'S.P.O.T. कांद्याच्या आतील भागाची तपासणी करतो का?',
      ta: 'S.P.O.T. வெங்காயத்தின் உட்பகுதியை ஆய்வு செய்கிறதா?'
    },
    a: {
      en: 'No. S.P.O.T. is an optical surface classifier. It evaluates external skin defects only. Internal flesh quality or concealed rot is out of scope.',
      hi: 'नहीं। S.P.O.T. केवल बाहरी सतह की जांच करता है। प्याज के आंतरिक गूदे या छिपी हुई सड़न की जांच इसमें शामिल नहीं है।',
      mr: 'नाही. S.P.O.T. केवळ बाह्य पृष्ठभागाची तपासणी करतो. कांद्याच्या आतील गराची तपासणी व्याप्तीबाहेर आहे.',
      ta: 'இல்லை. S.P.O.T. வெளிப்புற மேற்பரப்பை மட்டுமே ஆராய்கிறது. உட்பகுதி தரம் ஆராயப்படுவதில்லை.'
    }
  }
];

export const AssistantStep: React.FC<AssistantStepProps> = ({ onBack }) => {
  const { t, i18n } = useTranslation();
  const currentLang = (i18n.language ? i18n.language.substring(0, 2) : 'en') as 'en' | 'hi' | 'mr' | 'ta';

  const [selectedQuestion, setSelectedQuestion] = useState<string | null>(null);
  const [selectedAnswer, setSelectedAnswer] = useState<string | null>(null);
  const [isListening, setIsListening] = useState<boolean>(false);
  const [isSpeaking, setIsSpeaking] = useState<boolean>(false);
  const [voiceNotice, setVoiceNotice] = useState<string | null>(null);

  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (SpeechRecognition) {
      try {
        const recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        
        const langMap: Record<string, string> = { en: 'en-US', hi: 'hi-IN', mr: 'mr-IN', ta: 'ta-IN' };
        recognition.lang = langMap[currentLang] || 'en-US';

        recognition.onstart = () => {
          setIsListening(true);
          setVoiceNotice(null);
        };

        recognition.onresult = (event: any) => {
          setIsListening(false);
          const transcript = event.results[0][0].transcript.toLowerCase();
          handleVoiceQuery(transcript);
        };

        recognition.onerror = (event: any) => {
          setIsListening(false);
          if (event.error === 'not-allowed') {
            setVoiceNotice(t('speechBlocked'));
          } else {
            setVoiceNotice(`Voice capture note: ${event.error}. Please select a question below.`);
          }
        };

        recognition.onend = () => {
          setIsListening(false);
        };

        recognitionRef.current = recognition;
      } catch (err) {
        console.warn('SpeechRecognition init error', err);
      }
    }

    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort();
        } catch (_) {}
      }
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, [currentLang, t]);

  const handleVoiceQuery = (transcript: string) => {
    const matched = FAQ_KNOWLEDGE_BASE.find((item) => {
      const qText = (item.q[currentLang] || item.q.en).toLowerCase();
      return transcript.includes('grade') || transcript.includes('defect') || transcript.includes('quality') || qText.includes(transcript);
    }) || FAQ_KNOWLEDGE_BASE[0];

    handleSelectQA(matched);
  };

  const handleToggleListening = () => {
    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
    } else if (recognitionRef.current) {
      try {
        const langMap: Record<string, string> = { en: 'en-US', hi: 'hi-IN', mr: 'mr-IN', ta: 'ta-IN' };
        recognitionRef.current.lang = langMap[currentLang] || 'en-US';
        recognitionRef.current.start();
      } catch {
        setVoiceNotice(t('speechBlocked'));
      }
    } else {
      setVoiceNotice(t('voiceNotSupported'));
    }
  };

  const handleSelectQA = (item: QAItem) => {
    const q = item.q[currentLang] || item.q.en;
    const a = item.a[currentLang] || item.a.en;
    setSelectedQuestion(q);
    setSelectedAnswer(a);
    playSpeech(a);
  };

  const playSpeech = (text: string) => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.95;
      utterance.pitch = 1.0;
      const langMap: Record<string, string> = { en: 'en-US', hi: 'hi-IN', mr: 'mr-IN', ta: 'ta-IN' };
      utterance.lang = langMap[currentLang] || 'en-US';

      utterance.onstart = () => setIsSpeaking(true);
      utterance.onend = () => setIsSpeaking(false);
      utterance.onerror = () => setIsSpeaking(false);

      window.speechSynthesis.speak(utterance);
    }
  };

  const stopSpeech = () => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
    }
  };

  return (
    <div className="max-w-md mx-auto px-4 py-5 space-y-5 pb-24 font-sans text-[#163A2D]">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={onBack}
            className="p-2 rounded-xl border border-[#163A2D]/15 bg-white text-[#163A2D] active:scale-95 shadow-2xs cursor-pointer"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-xl font-black text-[#163A2D]">{t('voiceAssistantTitle')}</h1>
            <p className="text-xs text-[#163A2D]/70">{t('faqSubtitle')}</p>
          </div>
        </div>
      </div>

      {/* Hero Voice Interaction Card */}
      <div className="bg-[#163A2D] text-white rounded-3xl p-5 shadow-md border border-[#163A2D] text-center space-y-4">
        <div className="flex flex-col items-center space-y-2">
          <button
            onClick={handleToggleListening}
            aria-label={isListening ? 'Stop Listening' : 'Speak Question'}
            className={`w-18 h-18 rounded-full flex items-center justify-center text-white shadow-xl transition-all active:scale-90 cursor-pointer ${
              isListening
                ? 'bg-[#E51E3A] ring-8 ring-[#E51E3A]/30 animate-pulse'
                : 'bg-white/15 hover:bg-white/25 border-2 border-white/30'
            }`}
          >
            {isListening ? (
              <MicOff className="w-8 h-8 text-white" />
            ) : (
              <Mic className="w-8 h-8 text-white" />
            )}
          </button>

          <div>
            <span className="text-sm font-black text-white block">
              {isListening ? t('listening') : t('tapToSpeak')}
            </span>
            <span className="text-[11px] text-white/70 block mt-0.5">
              Ask about Grade-A, URS norms, or defect criteria
            </span>
          </div>
        </div>

        {voiceNotice && (
          <div className="bg-black/20 p-2.5 rounded-xl border border-white/10 text-[11px] text-amber-200">
            {voiceNotice}
          </div>
        )}
      </div>

      {/* Display Active QA Response */}
      {selectedAnswer && (
        <div className="bg-white border border-[#163A2D]/15 p-4 rounded-3xl shadow-md space-y-3 animate-in fade-in">
          <div className="flex items-start justify-between gap-2 border-b border-[#163A2D]/10 pb-2">
            <div className="flex items-center gap-2">
              <Bot className="w-4 h-4 text-[#E51E3A]" />
              <h3 className="text-xs font-black text-[#163A2D]">
                {selectedQuestion}
              </h3>
            </div>

            {isSpeaking ? (
              <button
                onClick={stopSpeech}
                className="p-1.5 bg-rose-50 text-[#E51E3A] rounded-lg text-[10px] font-bold flex items-center gap-1 cursor-pointer"
                title="Stop Audio"
              >
                <VolumeX className="w-3.5 h-3.5" />
                <span>Stop</span>
              </button>
            ) : (
              <button
                onClick={() => playSpeech(selectedAnswer)}
                className="p-1.5 bg-[#F7F1E7] text-[#163A2D] rounded-lg text-[10px] font-bold flex items-center gap-1 cursor-pointer"
                title="Play Audio"
              >
                <Volume2 className="w-3.5 h-3.5" />
                <span>Audio</span>
              </button>
            )}
          </div>

          <p className="text-xs text-[#163A2D]/90 leading-relaxed font-medium">
            {selectedAnswer}
          </p>
        </div>
      )}

      {/* FAQ Prompt Library */}
      <div className="space-y-2">
        <label className="block text-xs font-black uppercase tracking-wider text-[#163A2D] flex items-center gap-1.5">
          <HelpCircle className="w-4 h-4 text-[#E51E3A]" />
          <span>{t('faqTitle')}</span>
        </label>

        <div className="space-y-2">
          {FAQ_KNOWLEDGE_BASE.map((item, idx) => {
            const q = item.q[currentLang] || item.q.en;
            return (
              <button
                key={idx}
                onClick={() => handleSelectQA(item)}
                className="w-full p-3.5 bg-white border border-[#163A2D]/15 rounded-2xl text-left text-xs font-bold text-[#163A2D] hover:bg-[#F7F1E7] transition-all flex items-center justify-between shadow-2xs group cursor-pointer"
              >
                <span>{q}</span>
                <Sparkles className="w-3.5 h-3.5 text-[#163A2D]/40 group-hover:text-[#E51E3A] transition-colors shrink-0" />
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};
