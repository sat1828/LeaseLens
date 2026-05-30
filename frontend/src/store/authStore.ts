/**
 * Auth store.
 * BUG-27 FIX: Access token stored in module-level variable (in memory),
 *             NOT in localStorage. Stolen XSS cannot grab the token.
 *             Only non-sensitive user profile is persisted to localStorage.
 * BUG-28 FIX: refreshUser() called on App mount to sync server state.
 */
import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { api, setAuthToken } from '../api/client'

export interface AuthUser {
  id: string
  email: string
  full_name: string | null
  plan: 'FREE' | 'PRO' | 'TEAM'
  monthly_analysis_count: number
  total_analysis_count: number
  is_verified: boolean
  created_at: string
}

interface AuthState {
  user: AuthUser | null
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, fullName?: string) => Promise<void>
  logout: () => void
  refreshUser: () => Promise<void>
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isLoading: false,

      login: async (email, password) => {
        set({ isLoading: true })
        try {
          const { data } = await api.login(email, password)
          // BUG-27 FIX: token set in memory via api client, NOT localStorage
          setAuthToken(data.access_token)
          set({ user: data.user })
        } finally {
          set({ isLoading: false })
        }
      },

      register: async (email, password, fullName) => {
        set({ isLoading: true })
        try {
          const { data } = await api.register({ email, password, full_name: fullName })
          // BUG-27 FIX: token in memory only
          setAuthToken(data.access_token)
          set({ user: data.user })
        } finally {
          set({ isLoading: false })
        }
      },

      logout: () => {
        setAuthToken(null)   // clear in-memory token
        set({ user: null })
      },

      refreshUser: async () => {
        try {
          const { data } = await api.getMe()
          set({ user: data })
        } catch {
          // Token expired or invalid — clear state
          setAuthToken(null)
          set({ user: null })
        }
      },
    }),
    {
      name: 'll_auth_v2',
      // BUG-27 FIX: only persist user profile (no token — that's in memory)
      partialize: (state) => ({ user: state.user }),
    }
  )
)
