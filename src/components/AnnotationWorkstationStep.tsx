import React, { useState, useEffect, useRef } from 'react';
import {
  ShieldAlert,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  CheckCircle,
  AlertTriangle,
  ChevronLeft,
  ChevronRight,
  User,
  Trash2,
  Square,
  Lock,
  ArrowRight,
  Sparkles,
  Check,
  Undo2,
  Tag
} from 'lucide-react';
import {
  QueueItem,
  AnnotationRecord,
  EvidenceRegion,
  fetchAnnotationQueue,
  saveAnnotationRecord,
  getPilotImageUrl
} from '../api/annotation';

interface Props {
  onBackToApp?: () => void;
}

export const AnnotationWorkstationStep: React.FC<Props> = ({ onBackToApp }) => {
  // Annotator Identity
  const [annotatorId, setAnnotatorId] = useState<string>('HUMAN_ANNOTATOR_A');
  
  // Pilot Mode vs Full Queue
  const [pilotMode, setPilotMode] = useState<boolean>(true);
  const [showPilotCompleteModal, setShowPilotCompleteModal] = useState<boolean>(false);

  // Queue state
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [currentIndex, setCurrentIndex] = useState<number>(() => {
    const saved = sessionStorage.getItem('spot_annotation_pilot_index');
    if (saved !== null) {
      const parsed = parseInt(saved, 10);
      if (!isNaN(parsed) && parsed >= 0) return parsed;
    }
    return 0;
  });
  const [loading, setLoading] = useState<boolean>(true);
  const [saving, setSaving] = useState<boolean>(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Zoom & Pan
  const [zoomLevel, setZoomLevel] = useState<number>(1.0);
  const [drawMode, setDrawMode] = useState<boolean>(false);

  // Multi-label form state (DEFAULT BLANK for fresh ground-truth)
  const [healthy, setHealthy] = useState<boolean>(false);
  const [damage, setDamage] = useState<boolean>(false);
  const [rot, setRot] = useState<boolean>(false);
  const [sprout, setSprout] = useState<boolean>(false);
  const [uncertain, setUncertain] = useState<boolean>(false);
  
  const [uncertaintyReason, setUncertaintyReason] = useState<string>('');
  const [annotationConfidence, setAnnotationConfidence] = useState<'HIGH' | 'MEDIUM' | 'LOW'>('HIGH');
  const [notes, setNotes] = useState<string>('');
  
  // Evidence regions (bounding boxes drawn by human)
  const [evidenceRegions, setEvidenceRegions] = useState<EvidenceRegion[]>([]);
  const [isDrawing, setIsDrawing] = useState<boolean>(false);
  const [startPoint, setStartPoint] = useState<{ x: number; y: number } | null>(null);
  const [currentBox, setCurrentBox] = useState<[number, number, number, number] | null>(null);

  const imgRef = useRef<HTMLImageElement>(null);

  // Load queue on mount or annotator change
  useEffect(() => {
    loadQueue();
  }, [annotatorId]);

  const loadQueue = async () => {
    setLoading(true);
    try {
      const items = await fetchAnnotationQueue(annotatorId);
      setQueue(items);
      if (items.length > 0) {
        const savedIdxStr = sessionStorage.getItem('spot_annotation_pilot_index');
        let targetIdx = 0;
        const maxLen = pilotMode ? Math.min(10, items.length) : items.length;
        if (savedIdxStr !== null) {
          const parsed = parseInt(savedIdxStr, 10);
          if (!isNaN(parsed) && parsed >= 0 && parsed < maxLen) {
            targetIdx = parsed;
          }
        }
        setCurrentIndex(targetIdx);
        populateForm(items[targetIdx]);
      }
    } catch (err) {
      console.error("Failed to load queue:", err);
    } finally {
      setLoading(false);
    }
  };

  const activeQueue = pilotMode ? queue.slice(0, 10) : queue;
  const currentItem = activeQueue[currentIndex] || null;

  const populateForm = (item?: QueueItem | null) => {
    if (!item) return;
    const rec = item.record;
    if (rec) {
      // Load saved human annotation
      setHealthy(rec.multi_label_defects?.healthy || false);
      setDamage(rec.multi_label_defects?.damage || false);
      setRot(rec.multi_label_defects?.rot || false);
      setSprout(rec.multi_label_defects?.sprout || false);
      setUncertain(rec.multi_label_defects?.uncertain || false);
      setUncertaintyReason(rec.uncertainty_reason || '');
      setAnnotationConfidence(rec.annotation_confidence || 'HIGH');
      setNotes(rec.notes || '');
      setEvidenceRegions(rec.evidence_regions || []);
    } else {
      // RESET ALL STATE FOR FRESH UNLABELED IMAGE
      setHealthy(false);
      setDamage(false);
      setRot(false);
      setSprout(false);
      setUncertain(false);
      setUncertaintyReason('');
      setAnnotationConfidence('HIGH');
      setNotes('');
      setEvidenceRegions([]);
    }
    setZoomLevel(1.0);
    setDrawMode(false);
    setIsDrawing(false);
    setCurrentBox(null);
  };

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3000);
  };

  // Label Chip Toggles
  const handleToggleHealthy = () => {
    const nextVal = !healthy;
    setHealthy(nextVal);
    if (nextVal) {
      setDamage(false);
      setRot(false);
      setSprout(false);
      setUncertain(false);
      setUncertaintyReason('');
      setEvidenceRegions([]);
    }
  };

  const handleToggleDamage = () => {
    const nextVal = !damage;
    setDamage(nextVal);
    if (nextVal) setHealthy(false);
  };

  const handleToggleRot = () => {
    const nextVal = !rot;
    setRot(nextVal);
    if (nextVal) setHealthy(false);
  };

  const handleToggleSprout = () => {
    const nextVal = !sprout;
    setSprout(nextVal);
    if (nextVal) setHealthy(false);
  };

  const handleToggleUncertain = () => {
    const nextVal = !uncertain;
    setUncertain(nextVal);
    if (nextVal) setHealthy(false);
    if (!nextVal) setUncertaintyReason('');
  };

  // Drawing Handlers
  const handleMouseDown = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!drawMode || !imgRef.current) return;
    const rect = imgRef.current.getBoundingClientRect();
    const x = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    const y = Math.max(0, Math.min(1, (e.clientY - rect.top) / rect.height));
    setIsDrawing(true);
    setStartPoint({ x, y });
    setCurrentBox([x, y, x, y]);
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!isDrawing || !startPoint || !imgRef.current) return;
    const rect = imgRef.current.getBoundingClientRect();
    const x = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    const y = Math.max(0, Math.min(1, (e.clientY - rect.top) / rect.height));
    
    const x1 = Math.min(startPoint.x, x);
    const y1 = Math.min(startPoint.y, y);
    const x2 = Math.max(startPoint.x, x);
    const y2 = Math.max(startPoint.y, y);
    setCurrentBox([x1, y1, x2, y2]);
  };

  const handleMouseUp = () => {
    if (!isDrawing || !currentBox) return;
    setIsDrawing(false);
    setStartPoint(null);
    const [x1, y1, x2, y2] = currentBox;
    if (x2 - x1 > 0.02 && y2 - y1 > 0.02) {
      let activeDefectType: 'DAMAGE' | 'ROT' | 'SPROUT' | 'UNCERTAIN' = 'DAMAGE';
      if (rot) activeDefectType = 'ROT';
      else if (sprout) activeDefectType = 'SPROUT';
      else if (damage) activeDefectType = 'DAMAGE';
      else if (uncertain) activeDefectType = 'UNCERTAIN';
      else {
        activeDefectType = 'DAMAGE';
        setDamage(true);
        setHealthy(false);
      }
      const newRegion: EvidenceRegion = {
        region_id: `REG-${Date.now().toString().slice(-4)}`,
        defect_type: activeDefectType,
        region_format: 'BOUNDING_BOX',
        coordinates: [round4(x1), round4(y1), round4(x2), round4(y2)]
      };
      setEvidenceRegions(prev => [...prev, newRegion]);
      showToast('Evidence region drawn!');
    }
    setCurrentBox(null);
  };

  const round4 = (val: number) => Math.round(val * 10000) / 10000;

  const undoLastRegion = () => {
    setEvidenceRegions(prev => prev.slice(0, -1));
  };

  const clearAllRegions = () => {
    setEvidenceRegions([]);
  };

  const removeRegion = (idx: number) => {
    setEvidenceRegions(prev => prev.filter((_, i) => i !== idx));
  };

  // Save Annotation
  const handleSave = async (markNeedsReview: boolean = false) => {
    if (!currentItem) return;

    let isHealthy = healthy;
    let isDamage = damage;
    let isRot = rot;
    let isSprout = sprout;
    let isUncertain = uncertain || markNeedsReview;

    // Fallback: If evidence regions exist, ensure the appropriate defect is flagged
    if (!isHealthy && !isDamage && !isRot && !isSprout && !isUncertain && evidenceRegions.length > 0) {
      for (const reg of evidenceRegions) {
        if (reg.defect_type === 'DAMAGE') isDamage = true;
        else if (reg.defect_type === 'ROT') isRot = true;
        else if (reg.defect_type === 'SPROUT') isSprout = true;
        else if (reg.defect_type === 'UNCERTAIN') isUncertain = true;
        else isDamage = true;
      }
    }

    if (!markNeedsReview && !isHealthy && !isDamage && !isRot && !isSprout && !isUncertain) {
      alert("Validation Error: Please select at least one label (Healthy, Defect, or Uncertain) before saving.");
      return;
    }

    setSaving(true);
    try {
      const record: AnnotationRecord = {
        annotation_id: `ANN-${Date.now().toString().slice(-6)}`,
        image_id: currentItem.image_id,
        annotator_id: annotatorId,
        semantic_attributes: currentItem.semantic_attributes,
        multi_label_defects: {
          healthy: isHealthy,
          damage: isDamage,
          rot: isRot,
          sprout: isSprout,
          uncertain: isUncertain
        },
        size_assessment: {
          undersized_status: 'UNAVAILABLE',
          size_reference_available: false,
          estimated_diameter_mm: null,
          measurement_method: 'UNAVAILABLE'
        },
        evidence_regions: evidenceRegions,
        annotation_confidence: annotationConfidence,
        uncertainty_reason: isUncertain ? (uncertaintyReason || 'other') : undefined,
        notes: notes.trim() || undefined
      };

      const res = await saveAnnotationRecord(record);
      
      // Update local queue state
      const updatedQueue = [...queue];
      const targetIdx = queue.findIndex(q => q.image_id === currentItem.image_id);
      if (targetIdx !== -1) {
        updatedQueue[targetIdx] = {
          ...updatedQueue[targetIdx],
          annotation_status: markNeedsReview ? 'NEEDS_REVIEW' : res.annotation_status,
          record
        };
        setQueue(updatedQueue);
      }

      showToast(markNeedsReview ? 'Marked for Review & Saved' : 'Annotation Saved!');

      // Check pilot mode completion (10 images)
      if (pilotMode && currentIndex >= 9) {
        setShowPilotCompleteModal(true);
      } else if (currentIndex < activeQueue.length - 1) {
        const nextIdx = currentIndex + 1;
        sessionStorage.setItem('spot_annotation_pilot_index', String(nextIdx));
        setCurrentIndex(nextIdx);
        const nextItem = pilotMode ? updatedQueue.slice(0, 10)[nextIdx] : updatedQueue[nextIdx];
        if (nextItem) {
          populateForm(nextItem);
        } else if (activeQueue[nextIdx]) {
          populateForm(activeQueue[nextIdx]);
        }
      }
    } catch (err) {
      console.error("Save error:", err);
      alert("Failed to save annotation. Check backend connection.");
    } finally {
      setSaving(false);
    }
  };

  const handleNext = () => {
    if (currentIndex < activeQueue.length - 1) {
      const nextIdx = currentIndex + 1;
      sessionStorage.setItem('spot_annotation_pilot_index', String(nextIdx));
      setCurrentIndex(nextIdx);
      populateForm(activeQueue[nextIdx]);
    }
  };

  const handlePrev = () => {
    if (currentIndex > 0) {
      const prevIdx = currentIndex - 1;
      sessionStorage.setItem('spot_annotation_pilot_index', String(prevIdx));
      setCurrentIndex(prevIdx);
      populateForm(activeQueue[prevIdx]);
    }
  };

  // Image URL construction
  const imageUrl = currentItem ? getPilotImageUrl(currentItem.destination_filename) : '';
  const completedCount = activeQueue.filter(item => item.annotation_status === 'COMPLETE' || item.annotation_status === 'ADJUDICATED').length;
  const isSavedHumanAnnotation = Boolean(currentItem?.record);

  return (
    <div className="min-h-screen bg-stone-950 text-stone-100 flex flex-col font-sans pb-28 md:pb-8 max-w-7xl mx-auto">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed top-4 right-4 z-50 bg-emerald-600 text-white font-bold px-4 py-2.5 rounded-2xl shadow-2xl flex items-center gap-2 text-sm border border-emerald-400">
          <CheckCircle className="w-5 h-5 text-white" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* HEADER BANNER - Mobile First */}
      <header className="bg-stone-900 border-b border-stone-800 px-4 py-3 sticky top-0 z-30 flex items-center justify-between shadow-md">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-amber-500/10 border border-amber-500/30 rounded-xl">
            <ShieldAlert className="w-5 h-5 text-amber-400" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-black tracking-wider text-amber-400 uppercase">
                INTERNAL ANNOTATION WORKSTATION
              </span>
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                isSavedHumanAnnotation 
                  ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40' 
                  : 'bg-stone-800 text-stone-400 border-stone-700'
              }`}>
                {isSavedHumanAnnotation ? 'SAVED HUMAN ANNOTATION' : 'UNLABELED'}
              </span>
            </div>
            <p className="text-[11px] text-stone-400 font-mono mt-0.5">
              Human Ground-Truth Collection • NO AI CONFIDENCE • NO MODEL PREDICTIONS
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="hidden sm:flex items-center gap-2 bg-stone-800 px-3 py-1.5 rounded-xl border border-stone-700">
            <User className="w-3.5 h-3.5 text-emerald-400" />
            <select
              value={annotatorId}
              onChange={(e) => setAnnotatorId(e.target.value)}
              className="bg-transparent text-xs font-bold text-emerald-300 focus:outline-none cursor-pointer"
            >
              <option value="HUMAN_ANNOTATOR_A" className="bg-stone-900 text-stone-100">Annotator A</option>
              <option value="HUMAN_ANNOTATOR_B" className="bg-stone-900 text-stone-100">Annotator B</option>
            </select>
          </div>

          {onBackToApp && (
            <button
              onClick={onBackToApp}
              className="px-3 py-1.5 bg-stone-800 hover:bg-stone-700 text-stone-300 text-xs font-bold rounded-xl transition-colors border border-stone-700"
            >
              Back to Main App
            </button>
          )}
        </div>
      </header>

      {/* QUEUE PROGRESS BAR */}
      <div className="bg-stone-900/90 border-b border-stone-800/80 px-4 py-2.5 flex items-center justify-between text-xs">
        <div className="flex items-center gap-2">
          <button
            onClick={() => { setPilotMode(true); sessionStorage.setItem('spot_annotation_pilot_index', '0'); setCurrentIndex(0); if (queue.length > 0) populateForm(queue[0]); }}
            className={`px-2.5 py-1 rounded-lg text-xs font-bold transition-all ${
              pilotMode ? 'bg-amber-500 text-stone-950 shadow-md font-black' : 'text-stone-400 hover:text-stone-200'
            }`}
          >
            PILOT REVIEW (10)
          </button>
          <button
            onClick={() => { setPilotMode(false); sessionStorage.setItem('spot_annotation_pilot_index', '0'); setCurrentIndex(0); if (queue.length > 0) populateForm(queue[0]); }}
            className={`px-2.5 py-1 rounded-lg text-xs font-bold transition-all ${
              !pilotMode ? 'bg-amber-500 text-stone-950 shadow-md font-black' : 'text-stone-400 hover:text-stone-200'
            }`}
          >
            FULL QUEUE (100)
          </button>
        </div>

        <div className="flex items-center gap-3">
          <div className="hidden sm:block w-32 bg-stone-800 rounded-full h-2 overflow-hidden border border-stone-700">
            <div
              className="bg-emerald-400 h-full transition-all duration-300"
              style={{ width: `${activeQueue.length > 0 ? (completedCount / activeQueue.length) * 100 : 0}%` }}
            />
          </div>
          <span className="font-extrabold text-amber-400">
            Image {currentIndex + 1} of {activeQueue.length}
          </span>
        </div>
      </div>

      {/* MAIN CONTAINER */}
      {loading ? (
        <div className="flex-1 flex flex-col items-center justify-center p-12">
          <div className="w-10 h-10 border-4 border-amber-400 border-t-transparent rounded-full animate-spin mb-4" />
          <p className="text-stone-400 text-sm font-medium">Loading Pilot Images...</p>
        </div>
      ) : !currentItem ? (
        <div className="flex-1 flex flex-col items-center justify-center p-8 text-center">
          <AlertTriangle className="w-12 h-12 text-amber-500 mb-3" />
          <h3 className="text-lg font-bold text-stone-200">No Images Found in Queue</h3>
          <p className="text-xs text-stone-400 mt-1 max-w-md">Verify pilot dataset manifest at artifacts/ml/defect_annotations/pilot_100/manifest.csv</p>
        </div>
      ) : (
        <div className="flex-1 p-4 md:p-6 grid grid-cols-1 md:grid-cols-12 gap-6 items-start">

          {/* LEFT: IMAGE VIEWER & CANVAS (Mobile single column item 3) */}
          <div className="md:col-span-6 lg:col-span-7 bg-stone-900 rounded-3xl border border-stone-800 p-4 space-y-3 shadow-xl">
            {/* Image Header info & controls */}
            <div className="flex items-center justify-between text-xs">
              <div className="flex items-center gap-2">
                <span className="font-mono text-amber-300 font-bold bg-amber-950 px-2 py-0.5 rounded border border-amber-500/30">
                  {currentItem.image_id}
                </span>
                <span className="text-stone-400 font-mono text-[11px] truncate max-w-[180px] sm:max-w-none">
                  {currentItem.destination_filename}
                </span>
              </div>

              {/* Zoom & Draw Controls */}
              <div className="flex items-center gap-1.5">
                <button
                  onClick={() => setZoomLevel(z => Math.max(0.5, z - 0.2))}
                  className="p-1.5 bg-stone-800 hover:bg-stone-700 text-stone-300 rounded-xl border border-stone-700"
                  title="Zoom Out"
                >
                  <ZoomOut className="w-4 h-4" />
                </button>
                <span className="text-xs font-mono font-bold text-stone-300 px-1">{Math.round(zoomLevel * 100)}%</span>
                <button
                  onClick={() => setZoomLevel(z => Math.min(3.0, z + 0.2))}
                  className="p-1.5 bg-stone-800 hover:bg-stone-700 text-stone-300 rounded-xl border border-stone-700"
                  title="Zoom In"
                >
                  <ZoomIn className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setZoomLevel(1.0)}
                  className="p-1.5 bg-stone-800 hover:bg-stone-700 text-stone-300 rounded-xl border border-stone-700"
                  title="Reset Zoom"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            {/* Interactive Viewport */}
            <div
              className={`relative bg-stone-950 rounded-2xl overflow-hidden flex items-center justify-center p-2 min-h-[320px] sm:min-h-[420px] max-h-[60vh] border border-stone-800 ${
                drawMode ? 'cursor-crosshair' : 'cursor-default'
              }`}
              onMouseDown={handleMouseDown}
              onMouseMove={handleMouseMove}
              onMouseUp={handleMouseUp}
            >
              <div
                className="relative inline-block transition-transform duration-100 ease-out"
                style={{ transform: `scale(${zoomLevel})`, transformOrigin: 'center center' }}
              >
                <img
                  ref={imgRef}
                  src={imageUrl}
                  alt={currentItem.image_id}
                  className="max-h-[50vh] sm:max-h-[55vh] object-contain rounded-lg block select-none"
                  draggable={false}
                />

                {/* Render Human Drawn Evidence BBoxes */}
                {evidenceRegions.map((reg, idx) => {
                  const [x1, y1, x2, y2] = reg.coordinates;
                  return (
                    <div
                      key={reg.region_id || idx}
                      className="absolute border-2 border-amber-400 bg-amber-500/20 rounded-sm"
                      style={{
                        left: `${x1 * 100}%`,
                        top: `${y1 * 100}%`,
                        width: `${(x2 - x1) * 100}%`,
                        height: `${(y2 - y1) * 100}%`
                      }}
                    >
                      <span className="absolute -top-5 left-0 bg-amber-500 text-stone-950 font-black text-[10px] px-1.5 py-0.2 rounded shadow">
                        {reg.defect_type} #{idx + 1}
                      </span>
                    </div>
                  );
                })}

                {/* Render Active Drawing Box */}
                {currentBox && (
                  <div
                    className="absolute border-2 border-dashed border-emerald-400 bg-emerald-500/20"
                    style={{
                      left: `${currentBox[0] * 100}%`,
                      top: `${currentBox[1] * 100}%`,
                      width: `${(currentBox[2] - currentBox[0]) * 100}%`,
                      height: `${(currentBox[3] - currentBox[1]) * 100}%`
                    }}
                  />
                )}
              </div>
            </div>

            {/* Evidence Drawing Toolbar */}
            <div className="flex flex-wrap items-center justify-between gap-2 pt-1 border-t border-stone-800">
              <button
                onClick={() => setDrawMode(!drawMode)}
                className={`px-4 py-2 rounded-xl text-xs font-black flex items-center gap-2 transition-all ${
                  drawMode
                    ? 'bg-amber-500 text-stone-950 ring-2 ring-amber-300'
                    : 'bg-stone-800 hover:bg-stone-700 text-stone-200 border border-stone-700'
                }`}
              >
                <Square className="w-4 h-4" />
                <span>{drawMode ? 'DRAW MODE ACTIVE' : 'DRAW EVIDENCE'}</span>
              </button>

              {drawMode && (
                <span className="text-[11px] text-amber-300 font-medium animate-pulse">
                  Draw a rectangle over the visible defect on the image.
                </span>
              )}

              {evidenceRegions.length > 0 && (
                <div className="flex items-center gap-2">
                  <button
                    onClick={undoLastRegion}
                    className="px-2.5 py-1.5 bg-stone-800 hover:bg-stone-700 text-stone-300 rounded-xl text-xs font-bold flex items-center gap-1 border border-stone-700"
                  >
                    <Undo2 className="w-3.5 h-3.5" />
                    <span>Undo</span>
                  </button>
                  <button
                    onClick={clearAllRegions}
                    className="px-2.5 py-1.5 bg-rose-950/60 hover:bg-rose-900/80 text-rose-300 rounded-xl text-xs font-bold flex items-center gap-1 border border-rose-800/60"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                    <span>Clear</span>
                  </button>
                </div>
              )}
            </div>

            {/* Drawn Evidence Regions List */}
            {evidenceRegions.length > 0 && (
              <div className="bg-stone-950 p-3 rounded-2xl border border-stone-800 space-y-2">
                <span className="text-[11px] font-bold text-stone-400 uppercase tracking-wider block">
                  Drawn Evidence Regions ({evidenceRegions.length})
                </span>
                <div className="flex flex-wrap gap-2">
                  {evidenceRegions.map((reg, idx) => (
                    <div
                      key={reg.region_id || idx}
                      className="bg-stone-900 text-stone-200 px-3 py-1.5 rounded-xl border border-amber-500/40 text-xs flex items-center gap-2"
                    >
                      <span className="font-bold text-amber-400">{reg.defect_type}</span>
                      <span className="font-mono text-[10px] text-stone-400">[{reg.coordinates.join(', ')}]</span>
                      <button
                        onClick={() => removeRegion(idx)}
                        className="text-stone-400 hover:text-rose-400 p-0.5 ml-1"
                        title="Remove region"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* RIGHT: CONTROLS & LABELING PANEL (Mobile single column item 4-7) */}
          <div className="md:col-span-6 lg:col-span-5 space-y-5">
            
            {/* 1. MULTI-LABEL DEFECT CHIPS */}
            <div className="bg-stone-900 p-4 sm:p-5 rounded-3xl border border-stone-800 space-y-3 shadow-xl">
              <div className="flex items-center justify-between border-b border-stone-800 pb-2.5">
                <h3 className="text-sm font-black text-amber-400 uppercase tracking-wider flex items-center gap-2">
                  <Tag className="w-4 h-4 text-amber-400" />
                  <span>1. Multi-Label Defect Classification</span>
                </h3>
                <span className="text-[10px] text-stone-400 font-semibold">Select all that apply</span>
              </div>

              {/* Touch Chips */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                {/* Healthy Chip */}
                <button
                  id="label-healthy-btn"
                  data-testid="label-healthy-btn"
                  type="button"
                  onClick={handleToggleHealthy}
                  className={`p-3.5 rounded-2xl border text-left transition-all flex items-center justify-between min-h-[52px] cursor-pointer ${
                    healthy
                      ? 'bg-emerald-500/20 border-emerald-500 text-emerald-200 ring-2 ring-emerald-400'
                      : 'bg-stone-950 border-stone-800 text-stone-300 hover:border-stone-700'
                  }`}
                >
                  <div>
                    <span className="text-xs font-black block">Healthy</span>
                    <span className="text-[10px] text-stone-400 block font-normal">Grade A candidate • No defects</span>
                  </div>
                  <div className={`w-5 h-5 rounded-full border flex items-center justify-center ${
                    healthy ? 'bg-emerald-500 border-emerald-400 text-stone-950' : 'border-stone-700'
                  }`}>
                    {healthy && <Check className="w-3.5 h-3.5 stroke-[3]" />}
                  </div>
                </button>

                {/* Damaged Chip */}
                <button
                  id="label-damage-btn"
                  data-testid="label-damage-btn"
                  type="button"
                  onClick={handleToggleDamage}
                  className={`p-3.5 rounded-2xl border text-left transition-all flex items-center justify-between min-h-[52px] cursor-pointer ${
                    damage
                      ? 'bg-amber-500/20 border-amber-500 text-amber-200 ring-2 ring-amber-400'
                      : 'bg-stone-950 border-stone-800 text-stone-300 hover:border-stone-700'
                  }`}
                >
                  <div>
                    <span className="text-xs font-black block">Damaged</span>
                    <span className="text-[10px] text-stone-400 block font-normal">Cut / Bruise / Skin breakage</span>
                  </div>
                  <div className={`w-5 h-5 rounded-full border flex items-center justify-center ${
                    damage ? 'bg-amber-500 border-amber-400 text-stone-950' : 'border-stone-700'
                  }`}>
                    {damage && <Check className="w-3.5 h-3.5 stroke-[3]" />}
                  </div>
                </button>

                {/* Rotten Chip */}
                <button
                  id="label-rot-btn"
                  data-testid="label-rot-btn"
                  type="button"
                  onClick={handleToggleRot}
                  className={`p-3.5 rounded-2xl border text-left transition-all flex items-center justify-between min-h-[52px] cursor-pointer ${
                    rot
                      ? 'bg-rose-500/20 border-rose-500 text-rose-200 ring-2 ring-rose-400'
                      : 'bg-stone-950 border-stone-800 text-stone-300 hover:border-stone-700'
                  }`}
                >
                  <div>
                    <span className="text-xs font-black block">Rotten</span>
                    <span className="text-[10px] text-stone-400 block font-normal">Mold / Soft Rot / Decay</span>
                  </div>
                  <div className={`w-5 h-5 rounded-full border flex items-center justify-center ${
                    rot ? 'bg-rose-500 border-rose-400 text-stone-950' : 'border-stone-700'
                  }`}>
                    {rot && <Check className="w-3.5 h-3.5 stroke-[3]" />}
                  </div>
                </button>

                {/* Sprouted Chip */}
                <button
                  id="label-sprout-btn"
                  data-testid="label-sprout-btn"
                  type="button"
                  onClick={handleToggleSprout}
                  className={`p-3.5 rounded-2xl border text-left transition-all flex items-center justify-between min-h-[52px] cursor-pointer ${
                    sprout
                      ? 'bg-purple-500/20 border-purple-500 text-purple-200 ring-2 ring-purple-400'
                      : 'bg-stone-950 border-stone-800 text-stone-300 hover:border-stone-700'
                  }`}
                >
                  <div>
                    <span className="text-xs font-black block">Sprouted</span>
                    <span className="text-[10px] text-stone-400 block font-normal">Neck sprout / Green shoot</span>
                  </div>
                  <div className={`w-5 h-5 rounded-full border flex items-center justify-center ${
                    sprout ? 'bg-purple-500 border-purple-400 text-stone-950' : 'border-stone-700'
                  }`}>
                    {sprout && <Check className="w-3.5 h-3.5 stroke-[3]" />}
                  </div>
                </button>

                {/* Undersized Card (UNAVAILABLE Calibration Notice) */}
                <div className="p-3.5 rounded-2xl border border-stone-800/80 bg-stone-950/60 opacity-60 flex items-center justify-between min-h-[52px]">
                  <div>
                    <span className="text-xs font-bold text-stone-400 block">Undersized</span>
                    <span className="text-[10px] text-stone-500 block">UNAVAILABLE (No Ref Marker)</span>
                  </div>
                  <Lock className="w-4 h-4 text-stone-600" />
                </div>

                {/* Uncertain Chip */}
                <button
                  id="label-uncertain-btn"
                  data-testid="label-uncertain-btn"
                  type="button"
                  onClick={handleToggleUncertain}
                  className={`p-3.5 rounded-2xl border text-left transition-all flex items-center justify-between min-h-[52px] cursor-pointer ${
                    uncertain
                      ? 'bg-blue-500/20 border-blue-500 text-blue-200 ring-2 ring-blue-400'
                      : 'bg-stone-950 border-stone-800 text-stone-300 hover:border-stone-700'
                  }`}
                >
                  <div>
                    <span className="text-xs font-black block">Uncertain</span>
                    <span className="text-[10px] text-stone-400 block font-normal">Requires Expert Review</span>
                  </div>
                  <div className={`w-5 h-5 rounded-full border flex items-center justify-center ${
                    uncertain ? 'bg-blue-500 border-blue-400 text-stone-950' : 'border-stone-700'
                  }`}>
                    {uncertain && <Check className="w-3.5 h-3.5 stroke-[3]" />}
                  </div>
                </button>
              </div>

              {/* UNCERTAINTY WORKFLOW REASONS */}
              {uncertain && (
                <div className="bg-blue-950/40 p-3.5 rounded-2xl border border-blue-500/30 space-y-2 mt-3 animate-fadeIn">
                  <span className="text-xs font-bold text-blue-300 block">Why is this uncertain?</span>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    {[
                      { id: 'poor_visibility', label: 'Poor Visibility / Light' },
                      { id: 'shadow', label: 'Deep Shadow' },
                      { id: 'blur', label: 'Motion Blur / Focus' },
                      { id: 'occlusion', label: 'Partially Hidden' },
                      { id: 'ambiguous_defect', label: 'Ambiguous Mark' },
                      { id: 'other', label: 'Other Reason' }
                    ].map((reason) => (
                      <button
                        key={reason.id}
                        type="button"
                        onClick={() => setUncertaintyReason(reason.id)}
                        className={`p-2 rounded-xl text-left border transition-all text-[11px] font-medium ${
                          uncertaintyReason === reason.id
                            ? 'bg-blue-500 text-stone-950 font-bold border-blue-300'
                            : 'bg-stone-900 text-stone-300 border-stone-800 hover:border-blue-500/40'
                        }`}
                      >
                        {reason.label}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* 2. GROUND-TRUTH ANNOTATOR CONFIDENCE */}
            <div className="bg-stone-900 p-4 sm:p-5 rounded-3xl border border-stone-800 space-y-3 shadow-xl">
              <h3 className="text-xs font-black text-amber-400 uppercase tracking-wider">
                2. Ground-Truth Annotator Confidence
              </h3>
              <div className="grid grid-cols-3 gap-2.5">
                {(['HIGH', 'MEDIUM', 'LOW'] as const).map((conf) => (
                  <button
                    key={conf}
                    type="button"
                    onClick={() => setAnnotationConfidence(conf)}
                    className={`py-3 rounded-2xl text-xs font-black transition-all border min-h-[44px] ${
                      annotationConfidence === conf
                        ? conf === 'HIGH'
                          ? 'bg-emerald-500 text-stone-950 border-emerald-400 ring-2 ring-emerald-300'
                          : conf === 'MEDIUM'
                          ? 'bg-amber-500 text-stone-950 border-amber-400 ring-2 ring-amber-300'
                          : 'bg-rose-500 text-stone-950 border-rose-400 ring-2 ring-rose-300'
                        : 'bg-stone-950 text-stone-400 border-stone-800 hover:border-stone-700'
                    }`}
                  >
                    {conf}
                  </button>
                ))}
              </div>
            </div>

            {/* 3. OPTIONAL OBSERVATION NOTES */}
            <div className="bg-stone-900 p-4 sm:p-5 rounded-3xl border border-stone-800 space-y-2 shadow-xl">
              <label className="text-xs font-black text-amber-400 uppercase tracking-wider block">
                3. Annotator Notes (Optional)
              </label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Optional observation..."
                rows={2}
                className="w-full bg-stone-950 text-stone-200 p-3 rounded-2xl border border-stone-800 focus:outline-none focus:border-amber-500 text-xs placeholder-stone-600 resize-none"
              />
            </div>
          </div>
        </div>
      )}

      {/* STICKY BOTTOM ACTION BAR - Mobile First Thumb-Reach */}
      <div className="fixed bottom-0 left-0 right-0 z-40 bg-stone-900/95 backdrop-blur-md border-t border-stone-800 p-3 sm:px-6 flex items-center justify-between gap-3 shadow-2xl">
        <div className="flex items-center gap-2">
          <button
            id="nav-prev-btn"
            data-testid="nav-prev-btn"
            type="button"
            onClick={handlePrev}
            disabled={currentIndex === 0 || saving}
            className="px-3 py-3 bg-stone-800 hover:bg-stone-700 disabled:opacity-30 text-stone-200 text-xs font-bold rounded-2xl transition-colors border border-stone-700 flex items-center gap-1 min-h-[44px] cursor-pointer"
          >
            <ChevronLeft className="w-4 h-4" />
            <span className="hidden sm:inline">Prev</span>
          </button>

          <button
            id="nav-next-btn"
            data-testid="nav-next-btn"
            type="button"
            onClick={handleNext}
            disabled={currentIndex >= activeQueue.length - 1 || saving}
            className="px-3 py-3 bg-stone-800 hover:bg-stone-700 disabled:opacity-30 text-stone-200 text-xs font-bold rounded-2xl transition-colors border border-stone-700 flex items-center gap-1 min-h-[44px] cursor-pointer"
          >
            <span className="hidden sm:inline">Next</span>
            <ChevronRight className="w-4 h-4" />
          </button>

          <button
            id="needs-review-btn"
            data-testid="needs-review-btn"
            type="button"
            onClick={() => handleSave(true)}
            disabled={saving}
            className="px-3 py-3 bg-amber-950/80 hover:bg-amber-900 text-amber-300 text-xs font-bold rounded-2xl transition-colors border border-amber-600/50 flex items-center gap-1 min-h-[44px] cursor-pointer"
          >
            <AlertTriangle className="w-4 h-4 text-amber-400" />
            <span className="hidden sm:inline">Needs Review</span>
          </button>
        </div>

        <button
          id="save-next-btn"
          data-testid="save-next-btn"
          type="button"
          onClick={() => handleSave(false)}
          disabled={saving || !currentItem}
          className="flex-1 max-w-sm py-3.5 bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-400 hover:to-emerald-500 text-stone-950 font-black text-sm rounded-2xl transition-all shadow-lg flex items-center justify-center gap-2 active:scale-95 disabled:opacity-40 min-h-[48px] cursor-pointer"
        >
          {saving ? (
            <div className="w-5 h-5 border-2 border-stone-950 border-t-transparent rounded-full animate-spin" />
          ) : (
            <>
              <span>SAVE & NEXT IMAGE</span>
              <ArrowRight className="w-4 h-4 stroke-[3]" />
            </>
          )}
        </button>
      </div>

      {/* PILOT 10 COMPLETE MODAL */}
      {showPilotCompleteModal && (
        <div className="fixed inset-0 z-50 bg-stone-950/80 backdrop-blur-md flex items-center justify-center p-4">
          <div className="bg-stone-900 border-2 border-amber-500 p-6 rounded-3xl max-w-md w-full space-y-4 shadow-2xl text-center">
            <div className="w-12 h-12 bg-amber-500/20 text-amber-400 rounded-full flex items-center justify-center mx-auto border border-amber-500/40">
              <Sparkles className="w-6 h-6" />
            </div>
            <h3 className="text-xl font-black text-amber-400">PILOT REVIEW COMPLETE</h3>
            <p className="text-xs text-stone-300 leading-relaxed">
              You have completed human ground-truth annotation for the initial 10-image pilot set.
            </p>
            <div className="pt-2 flex flex-col gap-2">
              <button
                onClick={() => {
                  setShowPilotCompleteModal(false);
                  setPilotMode(false);
                  sessionStorage.setItem('spot_annotation_pilot_index', '10');
                  setCurrentIndex(10);
                  if (queue[10]) populateForm(queue[10]);
                }}
                className="w-full py-3 bg-amber-500 hover:bg-amber-400 text-stone-950 font-black text-xs rounded-xl transition-colors shadow-lg"
              >
                CONTINUE TO REMAINING 90 IMAGES
              </button>
              <button
                onClick={() => setShowPilotCompleteModal(false)}
                className="w-full py-2.5 bg-stone-800 hover:bg-stone-700 text-stone-300 font-bold text-xs rounded-xl transition-colors"
              >
                Close Modal
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
