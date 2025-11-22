/**
 * Custom API client wrapper with authentication
 *
 * Provides:
 * - Base URL configuration from environment
 * - Token storage utilities
 * - Authenticated client that auto-injects headers
 * - Automatic token refresh on 401 responses
 */

import { client } from './generated/client.gen';
import { attemptTokenRefresh } from './refresh-handler';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Token storage keys
const AUTH_TOKEN_KEY = 'auth_token';
const REFRESH_TOKEN_KEY = 'refresh_token';

/**
 * Configure the global API client with base URL
 * This sets the baseUrl for all generated SDK functions
 */
client.setConfig({
  baseUrl: API_URL,
});

/**
 * Setup response interceptor for automatic token refresh
 *
 * Intercepts 401 responses, attempts to refresh the access token,
 * and retries the original request with the new token.
 */
client.interceptors.response.use(async (response, request, options) => {
  // If response is 401 Unauthorized, try to refresh token
  if (response.status === 401) {
    // Don't retry if this is already the refresh endpoint
    if (request.url.includes('/api/v1/auth/refresh')) {
      return response;
    }

    // Attempt to refresh the access token
    const newAccessToken = await attemptTokenRefresh();

    if (newAccessToken) {
      // Clone the request with new authorization header
      const newHeaders = new Headers(request.headers);
      newHeaders.set('Authorization', `Bearer ${newAccessToken}`);

      // Retry the original request with new token
      const retryRequest = new Request(request, {
        headers: newHeaders,
      });

      const retryResponse = await fetch(retryRequest);
      return retryResponse;
    } else {
      // Refresh failed - redirect to login
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
    }
  }

  return response;
});

/**
 * Get auth token from localStorage
 */
export function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(AUTH_TOKEN_KEY);
}

/**
 * Get refresh token from localStorage
 */
export function getRefreshToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

/**
 * Save auth tokens to localStorage
 */
export function saveAuthTokens(accessToken: string, refreshToken: string): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(AUTH_TOKEN_KEY, accessToken);
  localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
}

/**
 * Remove auth tokens from localStorage
 */
export function clearAuthTokens(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(AUTH_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

/**
 * Get auth headers object
 */
export function getAuthHeaders(): Record<string, string> {
  const token = getAuthToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

/**
 * Extract error message from API error response
 * 
 * Extracts validation error messages from FastAPI error responses.
 * Falls back to generic message if no detailed error is available.
 * Strips prefixes like "Value error, " for cleaner user-facing messages.
 */
export function extractApiErrorMessage(error: unknown, fallbackMessage: string = 'An error occurred'): string {
  // Check if error has detail array (FastAPI validation error format)
  if (error && typeof error === 'object' && 'detail' in error) {
    const detail = (error as { detail?: unknown }).detail;
    
    // If detail is an array of validation errors
    if (Array.isArray(detail) && detail.length > 0) {
      const firstError = detail[0];
      if (firstError && typeof firstError === 'object' && 'msg' in firstError) {
        let message = firstError.msg as string;
        // Strip text before first comma (e.g., "Value error, " -> "")
        const commaIndex = message.indexOf(',');
        if (commaIndex !== -1) {
          message = message.substring(commaIndex + 1).trim();
        }
        return message;
      }
    }
    
    // If detail is a string (some endpoints return string detail)
    if (typeof detail === 'string') {
      let message = detail;
      // Strip text before first comma
      const commaIndex = message.indexOf(',');
      if (commaIndex !== -1) {
        message = message.substring(commaIndex + 1).trim();
      }
      return message;
    }
  }
  
  return fallbackMessage;
}

/**
 * Export base URL for direct fetch calls if needed
 */
export const API_BASE_URL = API_URL;
