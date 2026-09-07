/**
 * API Base Client for S.P.O.T. Backend services.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

export async function apiFetch<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      'Accept': 'application/json',
      ...(options.headers || {}),
    },
  });

  if (!response.ok) {
    let errorDetail = `API Request failed with status ${response.status}`;
    try {
      const errJson = await response.json();
      if (errJson.detail) {
        errorDetail = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
      }
    } catch {
      // Keep status code text if JSON parsing fails
    }
    throw new Error(errorDetail);
  }

  return response.json() as Promise<T>;
}

export function getApiUrl(): string {
  return API_BASE_URL;
}
