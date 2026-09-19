import React, { useRef, useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Camera, Upload, Volume2, RotateCcw, Sparkles, Check, RefreshCw, Cpu, WifiOff, Award, ArrowRight, AlertTriangle } from 'lucide-react';
import { ScanResult } from '../types';
import { playSuccessChime } from '../utils/soundEffects';
import { ScaleIntakeWidget } from './ScaleIntakeWidget';
import { edgeInferenceEngine } from '../utils/onnxInferenceEngine';
import { JUDGE_DEMO_SAMPLES, JudgeSampleItem } from '../data/judgeSamples';
import { getApiUrl } from '../api/client';

interface CameraStepProps {
  onCapture: (result: ScanResult) => void;
  onBack: () => void;
  onPlayVoice: (text: string) => void;
  judgeDemoMode?: boolean;
}

const SAMPLE_ONIONS = [
  {
    id: 'gradeA',
    labelKey: 'healthySample',
    color: '#4CAF50',
    grade: 'A' as const,
    score: 96,
    batchId: 'BATCH-MH-2026-891',
    centerId: 'APMC-NASHIK-CENTER-04',
    gradeAPercentage: 78.5,
    gradeURSPercentage: 15.2,
    rejectedPercentage: 6.3,
    moisture: '84% (Ideal)',
    firmness: 'Solid & Crisp',
    shelfLife: '45-60 Days',
    defectSummary: 'No moisture rot or fungal scale detected.',
    recommendation: 'Ideal for cold storage and export. NAFED procurement eligible.',
    bgColor: 'from-emerald-500 to-green-700',
    defectFlags: {
      damaged: false, damaged_count: 0,
      rotten: false, rotten_count: 0,
      sprouted: false, sprouted_count: 0,
      undersized: true, undersized_count: 3
    },
    weightDistribution: {
      total_batch_weight_kg: 100,
      grade_a_weight_kg: 78.5,
      grade_urs_weight_kg: 15.2,
      rejected_weight_kg: 6.3,
      grade_a_weight_percentage: 78.5,
      grade_urs_weight_percentage: 15.2,
      rejected_weight_percentage: 6.3
    }
  },
  {
    id: 'gradeURS',
    labelKey: 'fairSample',
    color: '#D97706',
    grade: 'URS' as const,
    score: 76,
    batchId: 'BATCH-MH-2026-432',
    centerId: 'APMC-PUNE-CENTER-02',
    gradeAPercentage: 42.0,
    gradeURSPercentage: 46.5,
    rejectedPercentage: 11.5,
    moisture: '89% (Slightly High)',
    firmness: 'Medium Firm',
    shelfLife: '15-20 Days',
    defectSummary: 'Minor surface black mold spot & size variation.',
    recommendation: 'Meets Government Under Relaxed Specifications (URS) norms. Sell in local market within 2 weeks.',
    bgColor: 'from-amber-500 to-amber-700',
    defectFlags: {
      damaged: true, damaged_count: 4,
      rotten: false, rotten_count: 0,
      sprouted: false, sprouted_count: 0,
      undersized: true, undersized_count: 7
    },
    weightDistribution: {
      total_batch_weight_kg: 100,
      grade_a_weight_kg: 42.0,
      grade_urs_weight_kg: 46.5,
      rejected_weight_kg: 11.5,
      grade_a_weight_percentage: 42.0,
      grade_urs_weight_percentage: 46.5,
      rejected_weight_percentage: 11.5
    }
  },
  {
    id: 'gradeC',
    labelKey: 'damagedSample',
    color: '#EF4444',
    grade: 'C' as const,
    score: 42,
    batchId: 'BATCH-MH-2026-109',
    centerId: 'APMC-SOLAPUR-CENTER-01',
    gradeAPercentage: 15.0,
    gradeURSPercentage: 25.0,
    rejectedPercentage: 60.0,
    moisture: '95% (Excess Water Rot)',
    firmness: 'Soft & Sprouted',
    shelfLife: '1-3 Days (Critical)',
    defectSummary: 'Neck rot, decay, and internal sprouting detected.',
    recommendation: 'Separate immediately from main batch to prevent decay propagation.',
    bgColor: 'from-rose-500 to-red-700',
    defectFlags: {
      damaged: true, damaged_count: 6,
      rotten: true, rotten_count: 5,
      sprouted: true, sprouted_count: 4,
      undersized: true, undersized_count: 9
    },
    weightDistribution: {
      total_batch_weight_kg: 100,
      grade_a_weight_kg: 15.0,
      grade_urs_weight_kg: 25.0,
      rejected_weight_kg: 60.0,
      grade_a_weight_percentage: 15.0,
      grade_urs_weight_percentage: 25.0,
      rejected_weight_percentage: 60.0
    }
  }
];

export const CameraStep: React.FC<CameraStepProps> = ({
  onCapture,
  onBack,
  onPlayVoice,
  judgeDemoMode = false,
}) => {
  const { t } = useTranslation();
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  const [cameraActive, setCameraActive] = useState<boolean>(false);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [capturedImageData, setCapturedImageData] = useState<string | null>(null);
  const [selectedSample, setSelectedSample] = useState<typeof SAMPLE_ONIONS[0] | null>(SAMPLE_ONIONS[0]);
  
  const [isScanning, setIsScanning] = useState<boolean>(false);
  const [scanProgress, setScanProgress] = useState<number>(0);
  const [batchWeightKg, setBatchWeightKg] = useState<number>(100.0);
  const [isOfflineInference, setIsOfflineInference] = useState<boolean>(!navigator.onLine);

  useEffect(() => {
    let currentStream: MediaStream | null = null;
    if (!judgeDemoMode && navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      navigator.mediaDevices
        .getUserMedia({ video: { facingMode: 'environment', width: { ideal: 1280 }, height: { ideal: 720 } } })
        .then((s) => {
          currentStream = s;
          if (videoRef.current) {
            videoRef.current.srcObject = s;
          }
          setCameraActive(true);
          setCameraError(null);
        })
        .catch((err) => {
          console.log('Camera hardware status notice:', err);
          setCameraActive(false);
          setCameraError('Live camera inactive. Use demo onions or upload photos below!');
        });
    }

    return () => {
      if (currentStream) {
        currentStream.getTracks().forEach((track) => track.stop());
      }
    };
  }, [judgeDemoMode]);

  const handleJudgeSampleSelect = (item: JudgeSampleItem) => {
    playSuccessChime();
    onPlayVoice(`Analyzing ${item.title}... Grade ${item.result.grade} lot detected.`);

    setIsScanning(true);
    setScanProgress(0);

    let currentPct = 0;
    const interval = setInterval(() => {
      currentPct += 25;
      if (currentPct >= 100) currentPct = 100;
      setScanProgress(currentPct);
    }, 60);

    setTimeout(() => {
      clearInterval(interval);
      setIsScanning(false);

      const res = { ...item.result };
      if (res.weightDistribution) {
        res.weightDistribution.total_batch_weight_kg = batchWeightKg;
        res.weightDistribution.grade_a_weight_kg = Math.round((batchWeightKg * (res.gradeAPercentage / 100)) * 10) / 10;
        res.weightDistribution.grade_urs_weight_kg = Math.round((batchWeightKg * (res.gradeURSPercentage / 100)) * 10) / 10;
        res.weightDistribution.rejected_weight_kg = Math.round((batchWeightKg * (res.rejectedPercentage / 100)) * 10) / 10;
      }
      onCapture(res);
    }, 350);
  };

  const handleCaptureLivePhoto = () => {
    playSuccessChime();
    onPlayVoice(t('scanCompleteConfirm'));

    let dataUrl: string | null = null;
    if (cameraActive && videoRef.current && canvasRef.current) {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      canvas.width = video.videoWidth || 640;
      canvas.height = video.videoHeight || 480;
      const ctx = canvas.getContext('2d');
      if (ctx) {
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        dataUrl = canvas.toDataURL('image/jpeg');
        setCapturedImageData(dataUrl);
      }
    }
    triggerScanningAnimation(dataUrl);
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      playSuccessChime();
      onPlayVoice(t('scanCompleteConfirm'));

      const file = e.target.files[0];
      const reader = new FileReader();
      reader.onload = (event) => {
        if (event.target?.result) {
          const imgData = event.target.result as string;
          setCapturedImageData(imgData);
          triggerScanningAnimation(imgData, file);
        }
      };
      reader.readAsDataURL(file);
    }
  };

  const [validationError, setValidationError] = useState<string | null>(null);

  const triggerScanningAnimation = async (imageData: string | null = null, uploadFile?: File) => {
    setValidationError(null);
    setIsScanning(true);
    setScanProgress(0);

    let currentPct = 0;
    const interval = setInterval(() => {
      currentPct += 15;
      if (currentPct >= 90) {
        currentPct = 90;
      }
      setScanProgress(currentPct);
    }, 60);

    let apiResponse: any = null;
    let edgeResult: ScanResult | null = null;
    let measuredLatencyMs = 0;
    const startPerf = performance.now();

    const isCurrentlyOffline = !navigator.onLine || isOfflineInference;

    if (isCurrentlyOffline) {
      console.log('⚡ Offline mode active: Running ONNX WebAssembly/WebGL edge inference...');
      edgeResult = await edgeInferenceEngine.runEdgeInference(
        imageData || 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxMDAiIGhlaWdodD0iMTAwIj48Y2lyY2xlIGN4PSI1MCIgY3k9IjUwIiByPSI0MCIgZmlsbD0iIzRFOTQ0RiIvPjwvc3ZnPg==',
        `BATCH-MH-2026-OFFLINE-${Math.floor(100 + Math.random() * 899)}`,
        'APMC-NASHIK-OFFLINE-01'
      );
      measuredLatencyMs = Math.round(performance.now() - startPerf);
    } else {
      try {
        const formData = new FormData();
        if (uploadFile) {
          formData.append('file', uploadFile);
        } else if (imageData) {
          const blob = await (await fetch(imageData)).blob();
          formData.append('file', blob, 'camera_capture.jpg');
        } else {
          const sampleBlob = new Blob(['mock_onion_photo'], { type: 'image/jpeg' });
          formData.append('file', sampleBlob, 'sample_onion.jpg');
        }

        const res = await fetch(`${getApiUrl()}/api/v1/analyze-onion`, {
          method: 'POST',
          body: formData,
        });

        measuredLatencyMs = Math.round(performance.now() - startPerf);

        if (res.status === 422) {
          const errData = await res.json().catch(() => ({}));
          const errorMsg = typeof errData.detail === 'object' && errData.detail?.message 
            ? errData.detail.message 
            : (typeof errData.detail === 'string' ? errData.detail : "This doesn't look like onions — please position onion bulbs within the camera frame and retake.");
          clearInterval(interval);
          setIsScanning(false);
          setValidationError(errorMsg);
          onPlayVoice("Quality validation notice: Please ensure onion bulbs are visible inside the frame and retake.");
          return;
        }

        if (res.ok) {
          apiResponse = await res.json();
        } else {
          throw new Error(`Server returned status ${res.status}`);
        }
      } catch (err) {
        console.log('FastAPI server call failed. Switching to ONNX WebAssembly Edge Inference fallback...', err);
        edgeResult = await edgeInferenceEngine.runEdgeInference(
          imageData || '',
          `BATCH-MH-2026-EDGE-${Math.floor(100 + Math.random() * 899)}`,
          'APMC-NASHIK-OFFLINE-01'
        );
        measuredLatencyMs = Math.round(performance.now() - startPerf);
      }
    }

    setScanProgress(100);
    clearInterval(interval);

    setTimeout(() => {
      setIsScanning(false);

      if (edgeResult) {
        edgeResult.weightDistribution = {
          total_batch_weight_kg: batchWeightKg,
          grade_a_weight_kg: Math.round((batchWeightKg * (edgeResult.gradeAPercentage / 100)) * 10) / 10,
          grade_urs_weight_kg: Math.round((batchWeightKg * (edgeResult.gradeURSPercentage / 100)) * 10) / 10,
          rejected_weight_kg: Math.round((batchWeightKg * (edgeResult.rejectedPercentage / 100)) * 10) / 10,
          grade_a_weight_percentage: edgeResult.gradeAPercentage,
          grade_urs_weight_percentage: edgeResult.gradeURSPercentage,
          rejected_weight_percentage: edgeResult.rejectedPercentage,
        };
        onCapture(edgeResult);
      } else if (apiResponse) {
        const rawGrade = apiResponse.overall_grade;
        let gradeType: 'A' | 'URS' | 'C' = 'A';
        if (rawGrade.includes('URS')) gradeType = 'URS';
        else if (rawGrade.includes('C')) gradeType = 'C';

        const result: ScanResult = {
          analysisId: apiResponse.analysis_id,
          batchId: apiResponse.batch_id || `BATCH-MH-2026-${Math.floor(100 + Math.random() * 899)}`,
          centerId: apiResponse.center_id || 'APMC-NASHIK-CENTER-04',
          grade: gradeType,
          overallGrade: apiResponse.overall_grade,
          qualityTitleKey: gradeType === 'A' ? 'gradeA' : gradeType === 'URS' ? 'gradeURS' : 'gradeC',
          score: Math.round(apiResponse.confidence_score),
          gradeAPercentage: apiResponse.grade_a_percentage,
          gradeURSPercentage: apiResponse.grade_urs_percentage,
          rejectedPercentage: apiResponse.rejected_percentage,
          defectFlags: apiResponse.defect_flags,
          weightDistribution: {
            total_batch_weight_kg: batchWeightKg,
            grade_a_weight_kg: Math.round((batchWeightKg * (apiResponse.grade_a_percentage / 100)) * 10) / 10,
            grade_urs_weight_kg: Math.round((batchWeightKg * (apiResponse.grade_urs_percentage / 100)) * 10) / 10,
            rejected_weight_kg: Math.round((batchWeightKg * (apiResponse.rejectedPercentage / 100)) * 10) / 10,
            grade_a_weight_percentage: apiResponse.grade_a_percentage,
            grade_urs_weight_percentage: apiResponse.grade_urs_percentage,
            rejected_weight_percentage: apiResponse.rejected_percentage,
          },
          boundingBoxes: apiResponse.bounding_boxes,
          moisture: apiResponse.moisture_level,
          firmness: apiResponse.firmness_rating,
          shelfLife: `${apiResponse.shelf_life_days} Days`,
          defectSummary: `Damaged: ${apiResponse.defect_flags?.damaged ? 'YES ('+apiResponse.defect_flags.damaged_count+')' : 'NO'} • Rotten: ${apiResponse.defect_flags?.rotten ? 'YES ('+apiResponse.defect_flags.rotten_count+')' : 'NO'} • Sprouted: ${apiResponse.defect_flags?.sprouted ? 'YES ('+apiResponse.defect_flags.sprouted_count+')' : 'NO'} • Undersized: ${apiResponse.defect_flags?.undersized ? 'YES ('+apiResponse.defect_flags.undersized_count+')' : 'NO'}`,
          recommendation: apiResponse.farmer_recommendation,
          imageUrl: imageData || '',
          timestamp: apiResponse.timestamp || new Date().toLocaleTimeString(),
          sha256Hash: apiResponse.sha256_hash,
          isInferenceEdge: false,
          serverLatencyMs: measuredLatencyMs,
          benchmarkLog: `[ONLINE FASTAPI SERVER BENCHMARK LOG]\n☁️ Server API Network Latency: ${measuredLatencyMs}ms\nDatabase Logging: SQLite Session Active`,
        };

        onCapture(result);
      } else {
        const activeSample = selectedSample || SAMPLE_ONIONS[0];
        const result: ScanResult = {
          batchId: activeSample.batchId,
          centerId: activeSample.centerId,
          grade: activeSample.grade,
          overallGrade: activeSample.grade === 'A' ? 'Grade-A' : activeSample.grade === 'URS' ? 'Grade-URS' : 'Grade-C',
          qualityTitleKey: activeSample.grade === 'A' ? 'gradeA' : activeSample.grade === 'URS' ? 'gradeURS' : 'gradeC',
          score: activeSample.score,
          gradeAPercentage: activeSample.gradeAPercentage,
          gradeURSPercentage: activeSample.gradeURSPercentage,
          rejectedPercentage: activeSample.rejectedPercentage,
          defectFlags: activeSample.defectFlags,
          weightDistribution: {
            total_batch_weight_kg: batchWeightKg,
            grade_a_weight_kg: Math.round((batchWeightKg * (activeSample.gradeAPercentage / 100)) * 10) / 10,
            grade_urs_weight_kg: Math.round((batchWeightKg * (activeSample.gradeURSPercentage / 100)) * 10) / 10,
            rejected_weight_kg: Math.round((batchWeightKg * (activeSample.rejectedPercentage / 100)) * 10) / 10,
            grade_a_weight_percentage: activeSample.gradeAPercentage,
            grade_urs_weight_percentage: activeSample.gradeURSPercentage,
            rejected_weight_percentage: activeSample.rejectedPercentage,
          },
          moisture: activeSample.moisture,
          firmness: activeSample.firmness,
          shelfLife: activeSample.shelfLife,
          defectSummary: activeSample.defectSummary,
          recommendation: activeSample.recommendation,
          imageUrl: imageData || '',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          isInferenceEdge: false,
          source: 'development_mock'
        };

        onCapture(result);
      }
    }, 300);
  };

  return (
    <div className="max-w-xl mx-auto px-4 py-6 space-y-6">
      {/* Top Banner Guide */}
      <div className="bg-[#1E3A2B] text-white p-4 rounded-3xl border-3 border-[#3A7D44] flex items-center justify-between shadow-lg">
        <div className="flex items-center gap-3">
          <button
            onClick={onBack}
            className="p-2 bg-[#2D5A27] rounded-xl hover:bg-[#3A7D44] active:scale-90 text-emerald-200"
          >
            <RotateCcw className="w-5 h-5" />
          </button>
          <div>
            <h2 className="text-lg font-bold flex items-center gap-2">
              <span>{judgeDemoMode ? '👑' : '📷'}</span> {judgeDemoMode ? 'Judge Instant Evaluation Mode' : t('cameraTitle')}
            </h2>
            <p className="text-xs text-emerald-200">
              {judgeDemoMode ? 'Select any pre-loaded batch below for instant end-to-end grading report' : t('cameraSubtitle')}
            </p>
          </div>
        </div>

        <button
          onClick={() => onPlayVoice(judgeDemoMode ? 'Judge Instant Evaluation Mode Active. Select a batch sample.' : `${t('cameraTitle')}. ${t('cameraSubtitle')}`)}
          className="p-2.5 bg-emerald-600 rounded-xl text-white hover:bg-emerald-500"
          title={t('listenInstruction')}
        >
          <Volume2 className="w-5 h-5" />
        </button>
      </div>

      {/* Real-time Quality Validation Error Notification */}
      {validationError && (
        <div
          role="alert"
          className="bg-rose-950/95 border-2 border-rose-500 text-white p-4 rounded-3xl flex items-start gap-3.5 shadow-2xl animate-shake"
        >
          <AlertTriangle className="w-6 h-6 text-rose-400 shrink-0 mt-0.5" />
          <div className="flex-1 space-y-2">
            <h4 className="text-sm font-black text-rose-200 uppercase tracking-wide">
              {t('retakeRequired') || 'Quality Screening: Retake Required'}
            </h4>
            <p className="text-xs text-rose-100 leading-relaxed font-medium">
              {validationError}
            </p>
            <button
              onClick={() => {
                setValidationError(null);
                setCapturedImageData(null);
              }}
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold rounded-xl transition-all shadow-md active:scale-95 border border-rose-400"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>{t('retakePhoto') || 'Retake Photo'}</span>
            </button>
          </div>
        </div>
      )}

      {/* JUDGE DEMO MODE SAMPLE SELECTOR VIEWPORT */}
      {judgeDemoMode ? (
        <div className="space-y-4">
          <div className="bg-gradient-to-br from-stone-900 via-amber-950/80 to-stone-900 text-white p-5 rounded-3xl border-3 border-amber-400 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b pb-3 border-amber-500/40">
              <div className="flex items-center gap-2">
                <Award className="w-6 h-6 text-yellow-300 animate-bounce" />
                <div>
                  <h3 className="text-base font-black text-amber-200 uppercase tracking-wide">
                    SIH 2026 Pre-Loaded Sample Batches
                  </h3>
                  <p className="text-[11px] text-stone-300">
                    Bypasses live hardware camera for fast multi-scenario evaluation
                  </p>
                </div>
              </div>
              <span className="text-[10px] font-black bg-amber-400 text-stone-950 px-2.5 py-1 rounded-full uppercase tracking-wider">
                4 Samples
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3" id="judge-sample-grid">
              {JUDGE_DEMO_SAMPLES.map((item) => (
                <button
                  key={item.id}
                  onClick={() => handleJudgeSampleSelect(item)}
                  id={`judge-sample-${item.id}`}
                  className="bg-stone-900 hover:bg-amber-950/90 active:scale-95 text-left p-4 rounded-2xl border-2 border-stone-700 hover:border-amber-400 shadow-lg transition-all flex flex-col justify-between space-y-3 group"
                >
                  <div className="flex items-start justify-between gap-2">
                    <span className="text-3xl">{item.icon}</span>
                    <span className={`text-[10px] font-black px-2 py-0.5 rounded-full uppercase tracking-wider border ${item.badgeBg}`}>
                      {item.badge}
                    </span>
                  </div>

                  <div>
                    <h4 className="text-sm font-extrabold text-white group-hover:text-amber-300 transition-colors">
                      {item.title}
                    </h4>
                    <p className="text-[11px] text-stone-300 mt-1 line-clamp-2 leading-tight">
                      {item.description}
                    </p>
                  </div>

                  <div className="pt-2 border-t border-stone-800 flex items-center justify-between text-xs font-bold text-emerald-400 group-hover:text-amber-200">
                    <span>Instantly Test Evaluation</span>
                    <ArrowRight className="w-4 h-4 transform group-hover:translate-x-1 transition-transform" />
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <>
          {/* Offline ONNX WebAssembly Mode Toggle Banner */}
          <div className="bg-stone-900 border-2 border-emerald-500/50 p-3.5 rounded-2xl flex items-center justify-between text-white shadow-md">
            <div className="flex items-center gap-2.5">
              <Cpu className="w-5 h-5 text-emerald-400 animate-pulse" />
              <div>
                <p className="text-xs font-black tracking-wide text-emerald-300">
                  ⚡ ONNX WebAssembly Edge Engine
                </p>
                <p className="text-[10px] text-stone-400">
                  {isOfflineInference
                    ? 'Offline Mode Active: Bypassing FastAPI server via in-browser WebAssembly'
                    : 'Auto-Switching: Fast API Server Engine Active'}
                </p>
              </div>
            </div>
            <button
              onClick={() => setIsOfflineInference(!isOfflineInference)}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1 border ${
                isOfflineInference
                  ? 'bg-amber-600 border-amber-400 text-white'
                  : 'bg-emerald-800 border-emerald-500 text-emerald-100 hover:bg-emerald-700'
              }`}
            >
              {isOfflineInference ? <WifiOff className="w-3.5 h-3.5" /> : <Cpu className="w-3.5 h-3.5" />}
              <span>{isOfflineInference ? 'Edge ONNX (Offline)' : 'Server FastAPI'}</span>
            </button>
          </div>

          <canvas ref={canvasRef} className="hidden" />

          {/* Camera Viewport Container */}
          <div className="relative bg-stone-900 rounded-3xl overflow-hidden border-4 border-[#2D5A27] aspect-[4/3] shadow-2xl flex items-center justify-center">
            {capturedImageData ? (
              <img
                src={capturedImageData}
                alt="Captured Onion"
                className="w-full h-full object-cover"
              />
            ) : cameraActive ? (
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="w-full h-full bg-gradient-to-br from-stone-900 via-[#102016] to-stone-900 p-6 flex flex-col items-center justify-center text-center relative">
                <div className={`w-36 h-36 rounded-full bg-gradient-to-br ${selectedSample?.bgColor || 'from-emerald-500 to-green-700'} border-4 border-white shadow-2xl flex items-center justify-center text-7xl animate-pulse`}>
                  🧅
                </div>
                <p className="mt-4 text-emerald-300 text-sm font-bold bg-emerald-950/80 px-4 py-1.5 rounded-full border border-emerald-500/40">
                  {selectedSample ? t(selectedSample.labelKey) : 'Demo Onion View'}
                </p>
                {cameraError && (
                  <p className="text-[11px] text-amber-200/90 mt-2 px-4 max-w-xs">
                    {cameraError}
                  </p>
                )}
              </div>
            )}

            {/* Circular Target & 45mm Scale Calibration Overlay Guide */}
            <div className="absolute inset-0 pointer-events-none flex flex-col items-center justify-center">
              <div className="mb-3 bg-black/75 backdrop-blur-md px-3.5 py-1.5 rounded-full border border-emerald-400/60 shadow-lg flex items-center gap-2">
                <div className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping" />
                <span className="text-[11px] font-black text-emerald-200 uppercase tracking-wide">
                  📏 45mm Scale Calibration Framing
                </span>
              </div>

              <div className="relative w-56 h-56 sm:w-64 sm:h-64 rounded-full border-4 border-dashed border-emerald-400 opacity-90 animate-pulse flex items-center justify-center shadow-[0_0_30px_rgba(76,175,80,0.5)]">
                <div className="absolute w-full h-[1px] bg-emerald-400/40" />
                <div className="absolute h-full w-[1px] bg-emerald-400/40" />
                <div className="w-40 h-40 rounded-full border-2 border-emerald-300/40 border-dotted" />

                <span className="text-white text-xs font-black tracking-wider bg-black/80 px-3.5 py-1.5 rounded-full backdrop-blur-md border border-emerald-400/50 shadow-md z-10">
                  🧅 {t('alignHere')}
                </span>
              </div>

              <span className="mt-3 text-[10px] font-bold text-amber-200 bg-stone-950/80 px-3 py-1 rounded-full border border-amber-500/40">
                Keep camera 15-20 cm above onion surface
              </span>
            </div>

            {/* Scanning Progress Overlay */}
            {isScanning && (
              <div className="absolute inset-0 bg-black/80 backdrop-blur-md flex flex-col items-center justify-center text-white z-20 space-y-4 px-6 text-center">
                <div className="relative">
                  <Sparkles className="w-16 h-16 text-emerald-400 animate-spin" />
                  <span className="absolute inset-0 flex items-center justify-center text-xs font-black text-emerald-200">
                    {scanProgress}%
                  </span>
                </div>
                <div>
                  <p className="text-2xl font-black tracking-wide text-emerald-300">
                    {isOfflineInference ? '⚡ ONNX Edge Inference' : t('scanning')}
                  </p>
                  <p className="text-xs text-amber-200/90 mt-1">
                    {isOfflineInference
                      ? 'Running WebAssembly / WebGL model inference (<1.5s target)...'
                      : 'Logging session to SQLite Database...'}
                  </p>
                  <div className="w-48 bg-stone-700 h-2.5 rounded-full overflow-hidden mt-3 mx-auto border border-emerald-400/40">
                    <div
                      className="bg-emerald-400 h-full transition-all duration-150 ease-out"
                      style={{ width: `${scanProgress}%` }}
                    />
                  </div>
                </div>
              </div>
            )}
          </div>

          {capturedImageData && !isScanning && (
            <button
              onClick={() => setCapturedImageData(null)}
              className="w-full py-3 bg-stone-200 hover:bg-stone-300 text-stone-800 rounded-2xl font-bold text-sm flex items-center justify-center gap-2 border border-stone-300"
            >
              <RefreshCw className="w-4 h-4" />
              <span>Clear Photo & Retake</span>
            </button>
          )}
        </>
      )}

      {/* RS-232 / USB Digital Weighing Scale Live Intake Widget */}
      <ScaleIntakeWidget
        currentWeightKg={batchWeightKg}
        onWeightChange={(newWeight) => setBatchWeightKg(newWeight)}
      />

      {!judgeDemoMode && (
        <>
          {/* Oversized Shutter Capture Button */}
          <div>
            <button
              disabled={isScanning}
              onClick={handleCaptureLivePhoto}
              className="w-full btn-oversized bg-[#2D5A27] hover:bg-[#1E3A2B] text-white py-5 px-6 rounded-3xl border-4 border-[#81C784] shadow-2xl active:scale-95 flex items-center justify-center gap-3 text-xl font-extrabold tracking-wide"
            >
              <Camera className="w-8 h-8 text-emerald-300" />
              <span>{t('takePhoto')}</span>
            </button>
          </div>

          {/* Demo Sample Selector Tiles */}
          <div className="bg-stone-100 p-4 rounded-3xl border-2 border-stone-300 space-y-3">
            <p className="text-xs font-bold text-stone-600 flex items-center gap-1.5">
              <span>💡</span> {t('orUseSample')}
            </p>
            <div className="grid grid-cols-3 gap-2">
              {SAMPLE_ONIONS.map((s) => {
                const isSel = selectedSample?.id === s.id;
                return (
                  <button
                    key={s.id}
                    onClick={() => {
                      setSelectedSample(s);
                      setCapturedImageData(null);
                    }}
                    className={`p-3 rounded-2xl border-3 text-left transition-all flex flex-col items-center text-center gap-1 relative ${
                      isSel
                        ? 'bg-white border-[#2D5A27] ring-2 ring-emerald-500 shadow-md'
                        : 'bg-stone-50 border-stone-200 hover:bg-white'
                    }`}
                  >
                    {isSel && (
                      <Check className="w-5 h-5 text-emerald-700 absolute top-1 right-1" />
                    )}
                    <span className="text-3xl">🧅</span>
                    <span className="text-[11px] font-extrabold text-stone-800 line-clamp-1">
                      {t(s.labelKey)}
                    </span>
                    <span
                      className="text-[10px] px-2 py-0.5 rounded-full font-bold text-white"
                      style={{ backgroundColor: s.color }}
                    >
                      Grade {s.grade}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Alternative Device File Upload Option */}
          <div className="text-center">
            <label className="inline-flex items-center gap-2 text-stone-700 bg-white border-2 border-stone-300 px-5 py-3 rounded-2xl font-bold text-sm hover:bg-stone-50 cursor-pointer shadow-sm active:scale-95">
              <Upload className="w-5 h-5 text-[#2D5A27]" />
              <span>{t('uploadPhoto')}</span>
              <input
                type="file"
                accept="image/*"
                className="hidden"
                onChange={handleFileUpload}
              />
            </label>
          </div>
        </>
      )}
    </div>
  );
};
