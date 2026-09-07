import React, { useEffect, useState } from 'react';
import { Loader2, CheckCircle2, ShieldCheck, Cpu } from 'lucide-react';
import { uploadInspectionImage, getCanonicalResult } from '../api/inspections';
import { CanonicalInspectionResult, NewInspectionMeta } from '../types';

interface AnalyzingStepProps {
  meta: NewInspectionMeta;
  file: File;
  onSuccess: (result: CanonicalInspectionResult) => void;
  onError: (errorMsg: string, status?: string) => void;
}

type StepKey = 'PREPARING' | 'QUALITY_GATE' | 'VISION_INFERENCE' | 'GRADING';

export const AnalyzingStep: React.FC<AnalyzingStepProps> = ({
  meta,
  file,
  onSuccess,
  onError,
}) => {
  const [currentStepIndex, setCurrentStepIndex] = useState<number>(0);
  const steps: { key: StepKey; label: string }[] = [
    { key: 'PREPARING', label: 'Preparing image payload' },
    { key: 'QUALITY_GATE', label: 'Checking image quality gate (blur, lighting)' },
    { key: 'VISION_INFERENCE', label: 'Executing optical onion detection' },
    { key: 'GRADING', label: 'Applying commercial grading policy' },
  ];

  useEffect(() => {
    let isSubscribed = true;

    async function executePipeline() {
      try {
        // Step 0: Preparing
        if (isSubscribed) setCurrentStepIndex(0);
        await new Promise((r) => setTimeout(r, 400));

        // Step 1: Quality Gate & Upload
        if (isSubscribed) setCurrentStepIndex(1);
        const uploadRes = await uploadInspectionImage({
          file,
          centerId: meta.procurement_center_id,
          batchId: meta.batch_id,
        });

        const reqId = uploadRes.request_id;
        const inspId = `INSP-${reqId}`;

        // Step 2: Vision Inference & Aggregation
        if (isSubscribed) setCurrentStepIndex(2);
        await new Promise((r) => setTimeout(r, 400));

        // Step 3: Grading & Canonical Result retrieval
        if (isSubscribed) setCurrentStepIndex(3);
        const canonicalResult = await getCanonicalResult(inspId);

        if (isSubscribed) {
          onSuccess(canonicalResult);
        }
      } catch (err: any) {
        if (isSubscribed) {
          onError(err.message || 'Inspection pipeline failed');
        }
      }
    }

    executePipeline();

    return () => {
      isSubscribed = false;
    };
  }, [file, meta, onSuccess, onError]);

  return (
    <div className="max-w-md mx-auto px-4 py-12 space-y-8 text-center">
      {/* Visual Spinner */}
      <div className="relative inline-flex items-center justify-center">
        <div className="w-24 h-24 rounded-full border-4 border-stone-200 border-t-[#2D5A27] animate-spin" />
        <Cpu className="w-8 h-8 text-[#2D5A27] absolute" />
      </div>

      <div className="space-y-2">
        <h2 className="text-xl font-bold text-[#0F281E]">Analyzing Sample Frame</h2>
        <p className="text-xs text-stone-500">Batch ID: {meta.batch_id}</p>
      </div>

      {/* Step State Indicator (No Fake Percentages) */}
      <div className="bg-white border border-stone-200 rounded-3xl p-5 shadow-sm text-left space-y-3.5">
        {steps.map((step, idx) => {
          const isDone = idx < currentStepIndex;
          const isCurrent = idx === currentStepIndex;
          return (
            <div key={step.key} className="flex items-center gap-3">
              {isDone ? (
                <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
              ) : isCurrent ? (
                <Loader2 className="w-5 h-5 text-[#2D5A27] animate-spin shrink-0" />
              ) : (
                <div className="w-5 h-5 rounded-full border-2 border-stone-200 shrink-0" />
              )}
              <span
                className={`text-xs font-semibold ${
                  isCurrent ? 'text-[#0F281E]' : isDone ? 'text-stone-700' : 'text-stone-400'
                }`}
              >
                {step.label}
              </span>
            </div>
          );
        })}
      </div>

      {/* Model Disclosure Badge */}
      <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-stone-100 border border-stone-200 rounded-full text-[11px] font-medium text-stone-600">
        <ShieldCheck className="w-3.5 h-3.5 text-amber-600" />
        <span>Development Mock Model Active — Test Double Only</span>
      </div>
    </div>
  );
};
