import { create } from 'zustand'
import { User } from '../types'
import apiClient from '../lib/apiClient'

interface AuthState {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, fullName?: string) => Promise<void>
  logout: () => Promise<void>
  fetchMe: () => Promise<void>
  initialize: () => Promise<void>
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  isLoading: true,
  isAuthenticated: false,

  initialize: async () => {
    const token = localStorage.getItem('access_token')
    if (!token) {
      set({ isLoading: false, isAuthenticated: false })
      return
    }
    try {
      await get().fetchMe()
    } catch {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      set({ isLoading: false, isAuthenticated: false, user: null })
    }
  },

  login: async (email: string, password: string) => {
    const response = await apiClient.post('/auth/login', { email, password })
    const { access_token, refresh_token } = response.data
    localStorage.setItem('access_token', access_token)
    localStorage.setItem('refresh_token', refresh_token)
    await get().fetchMe()
  },

  register: async (email: string, password: string, fullName?: string) => {
    await apiClient.post('/auth/register', {
      email,
      password,
      full_name: fullName || null,
    })
    await get().login(email, password)
  },

  logout: async () => {
    const refreshToken = localStorage.getItem('refresh_token')
    if (refreshToken) {
      try {
        await apiClient.post('/auth/logout', { refresh_token: refreshToken })
      } catch {
        // ignore errors on logout
      }
    }
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    set({ user: null, isAuthenticated: false })
  },

  fetchMe: async () => {
    const response = await apiClient.get('/auth/me')
    set({ user: response.data, isAuthenticated: true, isLoading: false })
  },
}))
