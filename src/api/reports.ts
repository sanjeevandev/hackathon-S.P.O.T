import { apiFetch, getApiUrl } from './client';
import { InspectionReport } from '../types';

export async function getInspectionReport(inspectionId: string): Promise<InspectionReport> {
  return apiFetch<InspectionReport>(`/api/v1/inspections/${encodeURIComponent(inspectionId)}/report?format=json`);
}

export function getInspectionReportHtmlUrl(inspectionId: string): string {
  return `${getApiUrl()}/api/v1/inspections/${encodeURIComponent(inspectionId)}/report?format=html`;
}

export async function generateInspectionReport(inspectionId: string): Promise<InspectionReport> {
  return apiFetch<InspectionReport>(`/api/v1/inspections/${encodeURIComponent(inspectionId)}/report`, {
    method: 'POST',
  });
}
