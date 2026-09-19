import React, { useEffect } from 'react';
import { ArrowRight } from 'lucide-react';

interface SplashStepProps {
  onEnter: () => void;
}

export const SplashStep: React.FC<SplashStepProps> = ({ onEnter }) => {
  useEffect(() => {
    const timer = setTimeout(() => {
      onEnter();
    }, 2000);
    return () => clearTimeout(timer);
  }, [onEnter]);

  return (
    <div className="fixed inset-0 z-50 bg-[#F7F1E7] text-[#163A2D] flex flex-col justify-between items-center p-6 text-center select-none overflow-hidden font-sans">
      {/* Top Brand Pill */}
      <div className="pt-8">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white border border-[#163A2D]/15 shadow-2xs">
          <span className="w-2 h-2 rounded-full bg-[#E51E3A] animate-pulse" />
          <span className="text-[11px] font-extrabold uppercase tracking-wider text-[#163A2D]">
            APMC AI Quality Inspection
          </span>
        </div>
      </div>

      {/* Center Hero Visual & Logo */}
      <div className="flex flex-col items-center max-w-xs space-y-6 my-auto">
        {/* Onion Emblem */}
        <div className="w-24 h-24 rounded-3xl bg-[#163A2D] text-white flex items-center justify-center text-5xl shadow-md border-2 border-[#163A2D]">
          🧅
        </div>

        {/* Brand Name & Full Title */}
        <div className="space-y-1.5">
          <h1 className="text-4xl font-black tracking-tight text-[#163A2D]">
            S.P.O.T.
          </h1>
          <p className="text-xs font-black text-[#E51E3A] uppercase tracking-wider">
            Smart Onion Quality Detector
          </p>
          <p className="text-xs text-[#163A2D]/70 italic pt-1 font-medium">
            "Detect • Analyze • Ensure Better Quality"
          </p>
        </div>

        {/* Technical Architecture Badge */}
        <div className="bg-white border border-[#163A2D]/15 rounded-2xl px-4 py-2 shadow-2xs text-[11px] text-[#163A2D] font-bold">
          YOLO26n-cls Vision Model • Optical Quality Classification
        </div>
      </div>

      {/* Bottom CTA */}
      <div className="w-full max-w-xs pb-6 space-y-3">
        <button
          onClick={onEnter}
          className="w-full py-4 px-6 bg-[#E51E3A] hover:bg-[#c91530] active:scale-[0.98] text-white rounded-2xl font-black shadow-md transition-all flex items-center justify-center gap-2 text-sm tracking-wide uppercase"
        >
          <span>Get Started</span>
          <ArrowRight className="w-4 h-4" />
        </button>

        <p className="text-[10px] text-[#163A2D]/50 font-bold tracking-wider uppercase">
          Autonomous Optical Grade Evaluation
        </p>
      </div>
    </div>
  );
};
