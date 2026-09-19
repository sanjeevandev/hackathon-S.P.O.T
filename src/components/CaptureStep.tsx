import React, { useRef, useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Camera, RefreshCw, ArrowRight, ArrowLeft, Sun, CheckCircle, Upload } from 'lucide-react';
import { NewInspectionMeta } from '../types';

interface CaptureStepProps {
  meta: NewInspectionMeta;
  onBack: () => void;
  onImageSelected: (file: File) => void;
}

export const CaptureStep: React.FC<CaptureStepProps> = ({
  meta,
  onBack,
  onImageSelected,
}) => {
  const { t } = useTranslation();
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const [stream, setStream] = useState<MediaStream | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [cameraError, setCameraError] = useState<string | null>(null);

  useEffect(() => {
    startCamera();
    return () => {
      stopCamera();
    };
  }, []);

  const startCamera = async () => {
    stopCamera();
    setCameraError(null);
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('Camera device API unavailable');
      }
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment', width: { ideal: 1920 }, height: { ideal: 1080 } },
        audio: false,
      });
      setStream(mediaStream);
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
      }
    } catch {
      setCameraError('Camera access unavailable. You can upload an onion photo from gallery.');
    }
  };

  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach((t) => t.stop());
      setStream(null);
    }
  };

  const handleCaptureFromCamera = () => {
    if (!videoRef.current) return;
    const video = videoRef.current;
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth || 1280;
    canvas.height = video.videoHeight || 720;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    canvas.toBlob((blob) => {
      if (blob) {
        const file = new File([blob], `capture-${Date.now()}.jpg`, { type: 'image/jpeg' });
        setSelectedFile(file);
        setPreviewUrl(URL.createObjectURL(file));
        stopCamera();
      }
    }, 'image/jpeg', 0.95);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      stopCamera();
    }
  };

  const handleRetake = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    startCamera();
  };

  const handleAnalyze = () => {
    if (selectedFile) {
      onImageSelected(selectedFile);
    }
  };

  // SCREEN: IMAGE CAPTURE REVIEW
  if (previewUrl && selectedFile) {
    return (
      <div className="max-w-md mx-auto px-4 py-5 space-y-5 pb-24 font-sans text-[#163A2D]">
        {/* Top Header */}
        <div className="flex items-center gap-3">
          <button
            onClick={handleRetake}
            className="p-2 rounded-xl border border-[#163A2D]/15 bg-white text-[#163A2D] active:scale-95 transition-all shadow-2xs"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-xl font-black text-[#163A2D]">Review Capture</h1>
            <p className="text-xs text-[#163A2D]/70">{t('batchIdLabel')}: <strong>{meta.batch_id}</strong></p>
          </div>
        </div>

        {/* Captured Image Display Card */}
        <div className="bg-[#163A2D] rounded-3xl overflow-hidden aspect-4/3 relative shadow-md border-2 border-[#163A2D]">
          <img
            src={previewUrl}
            alt="Captured Onion Sample"
            className="w-full h-full object-cover"
          />
          <div className="absolute top-3 right-3 px-3 py-1 bg-[#163A2D]/90 backdrop-blur-md rounded-full text-[10px] text-white font-bold flex items-center gap-1.5 border border-white/20">
            <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
            <span>Ready for Analysis</span>
          </div>
        </div>

        {/* Confirmation Message */}
        <div className="p-3.5 bg-white border border-[#163A2D]/15 rounded-2xl flex items-center gap-3 shadow-2xs">
          <div className="w-8 h-8 rounded-xl bg-[#163A2D] text-white flex items-center justify-center shrink-0">
            <CheckCircle className="w-5 h-5 text-emerald-400" />
          </div>
          <div>
            <div className="text-xs font-black text-[#163A2D]">
              Sample captured cleanly
            </div>
            <p className="text-[11px] text-[#163A2D]/75 mt-0.5 font-medium">
              Ready for optical defect classification and grading.
            </p>
          </div>
        </div>

        {/* Action Controls: RETAKE and ANALYZE */}
        <div className="grid grid-cols-2 gap-3 pt-1">
          <button
            onClick={handleRetake}
            className="min-h-[48px] py-3 px-4 bg-white text-[#163A2D] border border-[#163A2D]/20 rounded-2xl font-black hover:bg-[#F7F1E7] active:scale-95 transition-all flex items-center justify-center gap-2 text-xs uppercase tracking-wider shadow-2xs cursor-pointer"
          >
            <RefreshCw className="w-4 h-4 text-[#163A2D]/70" />
            <span>{t('retake')}</span>
          </button>

          <button
            onClick={handleAnalyze}
            className="min-h-[48px] py-3 px-4 bg-[#E51E3A] hover:bg-[#c91530] text-white rounded-2xl font-black shadow-md active:scale-95 transition-all flex items-center justify-center gap-2 text-xs uppercase tracking-wider cursor-pointer"
          >
            <span>{t('analyze')}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    );
  }

  // SCREEN: CAMERA SCANNER INTERFACE
  return (
    <div className="max-w-md mx-auto px-4 py-5 space-y-4 pb-24 font-sans text-[#163A2D]">
      {/* Top Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={onBack}
            className="p-2 rounded-xl border border-[#163A2D]/15 bg-white text-[#163A2D] active:scale-95 transition-all shadow-2xs cursor-pointer"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-xl font-black text-[#163A2D]">{t('cameraTitle')}</h1>
            <p className="text-xs text-[#163A2D]/70">{t('batchIdLabel')}: <strong>{meta.batch_id}</strong></p>
          </div>
        </div>
      </div>

      {/* Main Instruction Banner */}
      <div className="text-center">
        <p className="text-xs font-black text-[#163A2D] bg-white py-1.5 px-4 rounded-full inline-block border border-[#163A2D]/15 shadow-2xs">
          {t('cameraGuidance')}
        </p>
      </div>

      {/* Camera Viewport with Single-Onion Framing Guide */}
      <div className="bg-[#163A2D] rounded-3xl overflow-hidden aspect-4/3 relative flex items-center justify-center shadow-md border-2 border-[#163A2D]">
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className="w-full h-full object-cover"
        />

        {cameraError ? (
          <div className="absolute inset-0 bg-[#163A2D]/95 flex flex-col items-center justify-center p-6 text-center text-white space-y-3">
            <Camera className="w-10 h-10 text-white/60" />
            <p className="text-xs text-white/90">{cameraError}</p>
            <button
              onClick={() => fileInputRef.current?.click()}
              className="px-4 py-2 bg-[#E51E3A] hover:bg-[#c91530] text-white text-xs font-black uppercase rounded-xl shadow-md cursor-pointer"
            >
              {t('uploadPhoto')}
            </button>
          </div>
        ) : (
          /* Positioning Guide (NOT fake AI bounding box) */
          <div className="absolute inset-0 pointer-events-none flex flex-col items-center justify-center">
            <div className="w-44 h-44 border-2 border-dashed border-[#E51E3A] rounded-full shadow-[0_0_20px_rgba(229,30,58,0.35)] relative flex items-center justify-center">
              <span className="text-[9px] uppercase font-black tracking-widest text-white bg-[#163A2D]/90 px-2 py-0.5 rounded-full border border-white/20">
                Place 1 Onion Here
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Lighting Helper */}
      <div className="flex items-center justify-center gap-1.5 text-xs text-[#163A2D]/80 font-bold text-center">
        <Sun className="w-3.5 h-3.5 text-[#E51E3A]" />
        <span>{t('lightingHelper')}</span>
      </div>

      {/* Hidden File Input */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        onChange={handleFileChange}
        className="hidden"
      />

      {/* Bottom Scanning Controls */}
      <div className="flex items-center justify-center gap-8 pt-2">
        {/* Large Circular Capture Button */}
        <button
          onClick={handleCaptureFromCamera}
          disabled={Boolean(cameraError)}
          aria-label={t('capture')}
          className="w-20 h-20 rounded-full bg-[#E51E3A] hover:bg-[#c91530] text-white flex items-center justify-center shadow-lg active:scale-90 transition-all disabled:opacity-50 ring-4 ring-[#E51E3A]/25 cursor-pointer"
        >
          <div className="w-16 h-16 rounded-full border-2 border-white/80 flex items-center justify-center">
            <Camera className="w-8 h-8" />
          </div>
        </button>

        {/* Upload Button */}
        <button
          onClick={() => fileInputRef.current?.click()}
          className="flex flex-col items-center gap-1.5 p-3 rounded-2xl bg-white border border-[#163A2D]/15 text-[#163A2D] shadow-2xs hover:bg-[#F7F1E7] active:scale-95 transition-all min-w-[72px] cursor-pointer"
        >
          <Upload className="w-5 h-5 text-[#163A2D]" />
          <span className="text-[10px] font-black uppercase tracking-wider">{t('upload')}</span>
        </button>
      </div>
    </div>
  );
};
