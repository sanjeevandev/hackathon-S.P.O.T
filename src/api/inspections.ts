import { apiFetch, getApiUrl } from './client';
import { CanonicalInspectionResult, HistoryItem } from '../types';

export interface InspectImageOptions {
  file: File | Blob;
  centerId?: string;
  batchId?: string;
}

export async function uploadInspectionImage(options: InspectImageOptions): Promise<{ request_id: string; status: string; [key: string]: any }> {
  const formData = new FormData();
  formData.append('file', options.file, 'sample.jpg');

  const centerId = options.centerId || 'APMC-NASHIK-CENTER-04';
  const batchParam = options.batchId ? `&batch_id=${encodeURIComponent(options.batchId)}` : '';
  const url = `${getApiUrl()}/api/v1/inspect?center_id=${encodeURIComponent(centerId)}${batchParam}`;

  const response = await fetch(url, {
    method: 'POST',
    body: formData,
    headers: {
      'Accept': 'application/json',
    },
  });

  if (!response.ok) {
    let errText = `Upload failed with status ${response.status}`;
    try {
      const errJson = await response.json();
      if (errJson.detail) errText = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
    } catch {
      // Keep status
    }
    throw new Error(errText);
  }

  return response.json();
}

export async function getCanonicalResult(inspectionId: string): Promise<CanonicalInspectionResult> {
  return apiFetch<CanonicalInspectionResult>(`/api/v1/inspections/${encodeURIComponent(inspectionId)}/result`);
}

export async function getInspectionHistory(batchId?: string, limit: number = 50): Promise<HistoryItem[]> {
  const param = batchId ? `?batch_id=${encodeURIComponent(batchId)}&limit=${limit}` : `?limit=${limit}`;
  return apiFetch<HistoryItem[]>(`/api/v1/inspections${param}`);
}
