/**
 * S.P.O.T. Annotation Workstation API Client
 * Interfaces with internal backend annotation endpoints for ground truth collection.
 */

export interface QueueItem {
  image_id: string;
  source_path: string;
  destination_filename: string;
  semantic_attributes: {
    organ: string;
    color: string;
    arrangement: string;
  };
  audit_health_tag: string;
  annotation_status: 'UNLABELED' | 'IN_PROGRESS' | 'COMPLETE' | 'NEEDS_REVIEW' | 'ADJUDICATED';
  record?: AnnotationRecord | null;
}

export interface EvidenceRegion {
  region_id: string;
  defect_type: 'DAMAGE' | 'ROT' | 'SPROUT' | 'UNCERTAIN' | 'OTHER';
  region_format: 'BOUNDING_BOX';
  coordinates: [number, number, number, number]; // [x1, y1, x2, y2] normalized
}

export interface AnnotationRecord {
  annotation_id: string;
  image_id: string;
  annotator_id: string;
  semantic_attributes: {
    organ: string;
    color: string;
    arrangement: string;
  };
  multi_label_defects: {
    healthy: boolean;
    damage: boolean;
    rot: boolean;
    sprout: boolean;
    uncertain: boolean;
  };
  size_assessment: {
    undersized_status: 'UNAVAILABLE' | 'UNDERSIZED' | 'STANDARD';
    size_reference_available: boolean;
    estimated_diameter_mm: number | null;
    measurement_method: string;
  };
  evidence_regions: EvidenceRegion[];
  annotation_confidence: 'HIGH' | 'MEDIUM' | 'LOW';
  uncertainty_reason?: string;
  notes?: string;
}

export interface SaveAnnotationResponse {
  is_valid: boolean;
  errors: string[];
  annotation_status: 'COMPLETE' | 'NEEDS_REVIEW';
  record_id: string;
}

export interface Phase13Status {
  total_pilot: number;
  human_annotations_completed: number;
  remaining: number;
  needs_review: number;
  adjudicated: number;
  damage: number;
  rot: number;
  sprout: number;
  undersized: number;
  uncertain: number;
}

import { getApiUrl } from './client';

export async function fetchAnnotationQueue(annotatorId: string = 'HUMAN_ANNOTATOR_01'): Promise<QueueItem[]> {
  try {
    const res = await fetch(`${getApiUrl()}/api/annotation/queue?annotator_id=${encodeURIComponent(annotatorId)}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    return data.queue || [];
  } catch (err) {
    console.warn("Backend annotation API unavailable, using fallback pilot queue", err);
    return [];
  }
}

export async function fetchAnnotationProgress(annotatorId: string = 'HUMAN_ANNOTATOR_01') {
  try {
    const res = await fetch(`${getApiUrl()}/api/annotation/progress?annotator_id=${encodeURIComponent(annotatorId)}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    return { annotator_id: annotatorId, total_images: 100, completed: 0, remaining: 100, needs_review: 0, adjudicated: 0, completion_percentage: 0 };
  }
}

export async function saveAnnotationRecord(record: AnnotationRecord): Promise<SaveAnnotationResponse> {
  const res = await fetch(`${getApiUrl()}/api/annotation/save`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(record)
  });
  if (!res.ok) {
    throw new Error(`HTTP error ${res.status}`);
  }
  return await res.json();
}

export function getPilotImageUrl(destinationFilename: string): string {
  if (!destinationFilename) return '';
  return `${getApiUrl()}/api/annotation/pilot_image/${encodeURIComponent(destinationFilename)}`;
}
