/**
 * S.P.O.T. Environment-Aware API Base Client
 * Robust client supporting Web development, Android Capacitor WebView, and Offline Field Operations.
 */

const STORAGE_KEY = 'spot_api_base_url';

function resolveDefaultApiBaseUrl(): string {
  // 1. Check for manual runtime override in localStorage (allows runtime IP configuration on Android device)
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved && saved.trim().length > 0) {
      return saved.trim().replace(/\/+$/, '');
    }
  } catch {
    // LocalStorage may be restricted in some WebView contexts
  }

  // 2. Check Vite environment variables
  const envUrl = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL;
  if (envUrl && envUrl.trim().length > 0) {
    return envUrl.trim().replace(/\/+$/, '');
  }

  // 3. Detect environment
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    const isCapacitor =
      (window as any).Capacitor !== undefined ||
      window.location.origin.includes('capacitor://') ||
      (window.location.protocol === 'https:' && hostname === 'localhost' && window.location.port === '');

    if (isCapacitor) {
      // In native Android WebView / Emulator
      return 'http://10.0.2.2:8000';
    }

    // In live web browser (development with Vite proxy or production reverse proxy)
    // Relative path ensures zero CORS / host mismatch across localhost, 127.0.0.1, LAN IPs, or deployed domains.
    return '';
  }

  // 4. Default fallback
  return 'http://127.0.0.1:8000';
}

let activeApiBaseUrl: string = resolveDefaultApiBaseUrl();

export function getApiUrl(): string {
  return activeApiBaseUrl;
}

export function setApiUrl(newUrl: string): void {
  const sanitized = newUrl.trim().replace(/\/+$/, '');
  activeApiBaseUrl = sanitized;
  try {
    localStorage.setItem(STORAGE_KEY, sanitized);
  } catch {
    // Ignore storage errors
  }
}

export function resetApiUrl(): void {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch {
    // Ignore
  }
  activeApiBaseUrl = resolveDefaultApiBaseUrl();
}

export async function apiFetch<T>(endpoint: string, options: RequestInit = {}, timeoutMs: number = 8000): Promise<T> {
  const url = `${activeApiBaseUrl}${endpoint.startsWith('/') ? '' : '/'}${endpoint}`;
  
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, {
      ...options,
      signal: options.signal || controller.signal,
      headers: {
        'Accept': 'application/json',
        ...(options.headers || {}),
      },
    });

    clearTimeout(timeoutId);

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

    return (await response.json()) as T;
  } catch (err: any) {
    clearTimeout(timeoutId);
    if (err.name === 'AbortError') {
      throw new Error(`API Request timeout after ${timeoutMs / 1000}s. Server may be offline.`);
    }
    if (err.message && (err.message.includes('Failed to fetch') || err.message.includes('NetworkError'))) {
      const targetMsg = activeApiBaseUrl || 'relative host proxy (http://127.0.0.1:8000)';
      console.error(`[S.P.O.T. API] Connection failure to ${targetMsg}:`, err);
      throw new Error(`Backend server unreachable at ${targetMsg}. Ensure FastAPI backend is running on port 8000.`);
    }
    throw err;
  }
}

export async function checkBackendHealth(): Promise<{ ok: boolean; status?: string; details?: any }> {
  try {
    const res = await apiFetch<any>('/api/v1/health', {}, 5000);
    return { ok: true, status: 'online', details: res };
  } catch (err: any) {
    console.warn('[S.P.O.T. Health] Backend unavailable:', err.message || err);
    return { ok: false, status: 'offline', details: err.message };
  }
}

