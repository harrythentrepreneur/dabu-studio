/**
 * API Configuration
 * Centralizes all API endpoints and configuration
 * 
 * Set NEXT_PUBLIC_API_URL in your environment files:
 * - Development (.env.local): http://localhost:5001
 * - Production (.env.production): https://api.dabu.ai (or your Digital Ocean URL)
 */

// Get the API URL from environment variable (required in production)
export const API_URL = process.env.NEXT_PUBLIC_API_URL || '';

// API Endpoints
export const API_ENDPOINTS = {
  // Processing endpoints
  generateRequestId: `${API_URL}/api/generate-request-id`,
  process: `${API_URL}/api/process`,
  statusStream: (requestId: string) => `${API_URL}/api/status-stream/${requestId}`,

  // Download endpoints
  download: (requestId: string, type: string) => `${API_URL}/api/download/${requestId}/${type}`,

  // New download types for Intelligent CapCut service
  downloadCaptionedVideo: (requestId: string) => `${API_URL}/api/download/${requestId}/captioned_video`,
  downloadProjectBundle: (requestId: string) => `${API_URL}/api/download/${requestId}/project_bundle`,

  // Health check
  health: `${API_URL}/api/health`,
};

// Helper function to ensure URLs are absolute
export const ensureAbsoluteUrl = (url: string | undefined): string | undefined => {
  if (!url) return url;
  if (url.startsWith('http')) return url;
  return `${API_URL}${url}`;
};

export default API_ENDPOINTS;