/**
 * S.P.O.T. Centralized Production & Local API Configuration
 */

export const API_BASE_URL = 
  import.meta.env.VITE_API_URL || 
  (typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
    ? 'http://localhost:8000/api/v1'
    : '/api/v1');

export const FRONTEND_URL = 'https://spot-sih2026.vercel.app';
