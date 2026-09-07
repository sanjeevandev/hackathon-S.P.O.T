import React, { useRef, useState, useEffect } from 'react';
import { Camera, Upload, RefreshCw, ArrowRight, ArrowLeft, Sun, Focus, ShieldCheck } from 'lucide-react';
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
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment', width: { ideal: 1920 }, height: { ideal: 1080 } },
        audio: false,
      });
      setStream(mediaStream);
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
      }
    } catch (err: any) {
      setCameraError('Camera access unavailable. You can upload an image file directly.');
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
    }, 'image/jpeg', 0.92);
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

  const handleContinue = () => {
    if (selectedFile) {
      onImageSelected(selectedFile);
    }
  };

  return (
    <div className="max-w-xl mx-auto px-4 py-6 space-y-5">
      <div className="flex items-center gap-3">
        <button
          onClick={onBack}
          className="p-2 rounded-xl border border-stone-200 hover:bg-stone-100 text-stone-700"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div>
          <h1 className="text-xl font-bold text-[#0F281E]">Image Capture</h1>
          <p className="text-xs text-stone-500">Batch: <strong>{meta.batch_id}</strong></p>
        </div>
      </div>

      {/* Frame Guidance Box */}
      <div className="bg-[#0F281E]/5 border border-[#2D5A27]/20 rounded-2xl p-3.5 space-y-2 text-xs text-[#0F281E]">
        <div className="font-semibold flex items-center gap-1.5 text-[#2D5A27]">
          <Focus className="w-4 h-4" />
          <span>Optimum Image Quality Guidance</span>
        </div>
        <div className="grid grid-cols-2 gap-2 text-[11px] text-stone-600">
          <div className="flex items-center gap-1.5"><Sun className="w-3.5 h-3.5 text-amber-600" /> Adequate overhead light</div>
          <div className="flex items-center gap-1.5"><Focus className="w-3.5 h-3.5 text-[#2D5A27]" /> Hold phone steady</div>
          <div className="flex items-center gap-1.5"><ShieldCheck className="w-3.5 h-3.5 text-blue-600" /> Avoid extreme overlap</div>
          <div className="flex items-center gap-1.5"><Camera className="w-3.5 h-3.5 text-stone-600" /> Fill frame with onions</div>
        </div>
      </div>

      {/* Camera / Preview Viewport */}
      <div className="bg-black rounded-3xl overflow-hidden aspect-[4/3] relative flex items-center justify-center shadow-lg border-4 border-[#2D5A27]">
        {previewUrl ? (
          <img src={previewUrl} alt="Captured Sample" className="w-full h-full object-cover" />
        ) : (
          <>
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className="w-full h-full object-cover"
            />
            {cameraError && (
              <div className="absolute inset-0 bg-stone-900/90 flex flex-col items-center justify-center p-6 text-center text-white space-y-3">
                <Camera className="w-10 h-10 text-stone-400" />
                <p className="text-xs text-stone-300">{cameraError}</p>
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="px-4 py-2 bg-[#2D5A27] text-white text-xs font-bold rounded-xl"
                >
                  Upload Image File
                </button>
              </div>
            )}
          </>
        )}

        {/* Viewport Overlay Framing Lines */}
        {!previewUrl && !cameraError && (
          <div className="absolute inset-4 border-2 border-dashed border-white/40 rounded-2xl pointer-events-none flex items-center justify-center">
            <span className="text-[10px] uppercase tracking-wider text-white/70 bg-black/40 px-2 py-1 rounded">
              Position Onions in Frame
            </span>
          </div>
        )}
      </div>

      {/* Hidden File Input */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        onChange={handleFileChange}
        className="hidden"
      />

      {/* Action Controls */}
      <div className="space-y-3">
        {!previewUrl ? (
          <div className="grid grid-cols-2 gap-3">
            <button
              onClick={handleCaptureFromCamera}
              disabled={Boolean(cameraError)}
              className="py-3.5 px-4 bg-[#2D5A27] text-white rounded-2xl font-bold shadow-md hover:bg-[#23471F] disabled:opacity-50 transition-all flex items-center justify-center gap-2"
            >
              <Camera className="w-5 h-5" />
              <span>CAPTURE</span>
            </button>
            <button
              onClick={() => fileInputRef.current?.click()}
              className="py-3.5 px-4 bg-white text-[#0F281E] border border-stone-300 rounded-2xl font-bold hover:bg-stone-50 transition-all flex items-center justify-center gap-2"
            >
              <Upload className="w-5 h-5 text-stone-600" />
              <span>UPLOAD</span>
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-3">
            <button
              onClick={handleRetake}
              className="py-3.5 px-4 bg-white text-stone-700 border border-stone-300 rounded-2xl font-bold hover:bg-stone-50 transition-all flex items-center justify-center gap-2"
            >
              <RefreshCw className="w-5 h-5 text-stone-500" />
              <span>RETAKE</span>
            </button>
            <button
              onClick={handleContinue}
              className="py-3.5 px-4 bg-[#2D5A27] text-white rounded-2xl font-bold shadow-md hover:bg-[#23471F] transition-all flex items-center justify-center gap-2"
            >
              <span>CONTINUE</span>
              <ArrowRight className="w-5 h-5" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
