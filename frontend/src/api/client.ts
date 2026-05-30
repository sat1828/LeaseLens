/**
 * Axios API client.
 * BUG-27 FIX: Token stored in module-level variable (in memory), not localStorage.
 *             setAuthToken() exported so authStore can set it after login/register.
 * BUG-37 FIX: 401 interceptor skips /auth/ endpoints to prevent redirect loops.
 */
import axios from 'axios'
import toast from 'react-hot-toast'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// BUG-27 FIX: In-memory token — never touches localStorage
let _inMemoryToken: string | null = null

export function setAuthToken(token: string | null): void {
  _inMemoryToken = token
}

export function getAuthToken(): string | null {
  return _inMemoryToken
}

export const apiClient = axios.create({
  baseURL: `${API_BASE}/api/v1`,
  timeout: 120000,   // 2 min for analysis endpoint
})

// Attach token from memory on every request
apiClient.interceptors.request.use((config) => {
  const token = _inMemoryToken
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Global response error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const status   = error.response?.status
    const detail   = error.response?.data?.detail
    const reqUrl   = error.config?.url || ''

    if (status === 401) {
      // BUG-37 FIX: never redirect on auth-endpoint 401s (wrong password etc.)
      const isAuthEndpoint = reqUrl.includes('/auth/')
      if (!isAuthEndpoint) {
        _inMemoryToken = null
        if (!window.location.pathname.includes('/login')) {
          window.location.href = '/login'
        }
      }
    } else if (status === 429) {
      toast.error(detail || 'Quota exceeded. Upgrade to Pro for unlimited analyses.')
    } else if (status === 503) {
      toast.error(detail || 'AI service temporarily unavailable. Please retry in 30 seconds.')
    }
    // 500s: let the calling code handle — don't show a generic toast here

    return Promise.reject(error)
  }
)

// Typed API surface
export const api = {
  // Auth
  register: (data: { email: string; password: string; full_name?: string }) =>
    apiClient.post('/auth/register', data),

  login: (email: string, password: string) => {
    const form = new FormData()
    form.append('username', email)
    form.append('password', password)
    return apiClient.post('/auth/login', form)
  },

  getMe: () => apiClient.get('/auth/me'),

  verifyEmail: (token: string) =>
    apiClient.get(`/auth/verify-email?token=${token}`),

  resendVerification: () =>
    apiClient.post('/auth/resend-verification'),

  forgotPassword: (email: string) => {
    const form = new FormData()
    form.append('email', email)
    return apiClient.post('/auth/forgot-password', form)
  },

  resetPassword: (token: string, newPassword: string) => {
    const form = new FormData()
    form.append('token', token)
    form.append('new_password', newPassword)
    return apiClient.post('/auth/reset-password', form)
  },

  changePassword: (currentPassword: string, newPassword: string) =>
    apiClient.post('/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    }),

  deleteAccount: () => apiClient.delete('/auth/account'),

  // Analysis
  analyzeFile: (file: File, jurisdiction: string) => {
    const form = new FormData()
    form.append('file', file)
    form.append('jurisdiction', jurisdiction)
    return apiClient.post('/analyze/', form)
  },

  analyzeText: (text: string, jurisdiction: string) => {
    const form = new FormData()
    form.append('lease_text', text)
    form.append('jurisdiction', jurisdiction)
    return apiClient.post('/analyze/', form)
  },

  getHistory: (limit = 20, offset = 0) =>
    apiClient.get(`/analyze/history?limit=${limit}&offset=${offset}`),

  getAnalysis: (id: string) => apiClient.get(`/analyze/${id}`),

  deleteAnalysis: (id: string) => apiClient.delete(`/analyze/${id}`),

  // Payments
  getPlans:       ()           => apiClient.get('/payments/plans'),
  createCheckout: (plan: string) => apiClient.post(`/payments/checkout/${plan}`),
  createPortal:   ()           => apiClient.post('/payments/portal'),
}
