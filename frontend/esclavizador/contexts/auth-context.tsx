"use client"

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import type { UserResponse } from '@/lib/api/generated'
import {
  loginApiV1AuthLoginPost,
  registerApiV1AuthRegisterPost,
  logoutApiV1AuthLogoutPost,
  getMeApiV1AuthMeGet
} from '@/lib/api/generated'
import {
  saveAuthTokens,
  clearAuthTokens,
  getAuthToken,
  getRefreshToken,
  getAuthHeaders
} from '@/lib/api/client'

interface AuthContextType {
  user: UserResponse | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, organizationName: string) => Promise<void>
  logout: () => Promise<void>
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const router = useRouter()

  // Fetch current user from backend
  const refreshUser = useCallback(async () => {
    const token = getAuthToken()
    if (!token) {
      setUser(null)
      setIsLoading(false)
      return
    }

    try {
      const { data, error } = await getMeApiV1AuthMeGet({
        headers: getAuthHeaders(),
      })

      if (error || !data) {
        clearAuthTokens()
        setUser(null)
      } else {
        setUser(data)
      }
    } catch (err) {
      console.error('Failed to fetch user:', err)
      clearAuthTokens()
      setUser(null)
    } finally {
      setIsLoading(false)
    }
  }, [])

  // Load user on mount
  useEffect(() => {
    refreshUser()
  }, [refreshUser])

  const login = async (email: string, password: string) => {
    setIsLoading(true)
    try {
      const { data, error } = await loginApiV1AuthLoginPost({
        body: { email, password },
      })

      if (error || !data) {
        throw new Error('Login failed')
      }

      saveAuthTokens(data.access_token, data.refresh_token)
      await refreshUser()
      router.push('/')
    } catch (err) {
      setIsLoading(false)
      throw err
    }
  }

  const register = async (email: string, password: string, organizationName: string) => {
    setIsLoading(true)
    try {
      const { data, error } = await registerApiV1AuthRegisterPost({
        body: {
          email,
          password,
          organization_name: organizationName,
          role: 'boss',
        },
      })

      if (error || !data) {
        throw new Error('Registration failed')
      }

      // Registration successful - now log in automatically
      await login(email, password)
    } catch (err) {
      setIsLoading(false)
      throw err
    }
  }

  const logout = async () => {
    const refreshToken = getRefreshToken()

    if (refreshToken) {
      try {
        await logoutApiV1AuthLogoutPost({
          headers: getAuthHeaders(),
          body: { refresh_token: refreshToken },
        })
      } catch (err) {
        console.error('Logout API call failed:', err)
      }
    }

    clearAuthTokens()
    setUser(null)
    router.push('/login')
  }

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    register,
    logout,
    refreshUser,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuthContext() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuthContext must be used within an AuthProvider')
  }
  return context
}
