import { refreshApiV1AuthRefreshPost } from './generated'
import { getRefreshToken, saveAuthTokens, clearAuthTokens } from './client'

let isRefreshing = false
let refreshPromise: Promise<string | null> | null = null

/**
 * Attempts to refresh the access token using the stored refresh token.
 *
 * Handles race conditions by ensuring only one refresh happens at a time.
 * Multiple simultaneous calls will wait for the same refresh promise.
 *
 * @returns New access token on success, null on failure
 */
export async function attemptTokenRefresh(): Promise<string | null> {
  // If already refreshing, return the existing promise
  if (isRefreshing && refreshPromise) {
    return refreshPromise
  }

  // Set refreshing flag and create new promise
  isRefreshing = true
  refreshPromise = performTokenRefresh()

  try {
    const result = await refreshPromise
    return result
  } finally {
    // Reset flags after completion
    isRefreshing = false
    refreshPromise = null
  }
}

/**
 * Performs the actual token refresh API call.
 * @returns New access token on success, null on failure
 */
async function performTokenRefresh(): Promise<string | null> {
  const refreshToken = getRefreshToken()

  if (!refreshToken) {
    // No refresh token available - user needs to log in
    clearAuthTokens()
    return null
  }

  try {
    const { data, error } = await refreshApiV1AuthRefreshPost({
      body: {
        refresh_token: refreshToken,
      },
    })

    if (error || !data) {
      // Refresh failed - token might be expired or revoked
      clearAuthTokens()
      return null
    }

    // Save new access token (keep existing refresh token)
    saveAuthTokens(data.access_token, refreshToken)

    return data.access_token
  } catch (err) {
    // Network error or other issue
    console.error('Token refresh failed:', err)
    clearAuthTokens()
    return null
  }
}
