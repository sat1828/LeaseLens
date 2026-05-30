/**
 * Authentication modal (login + register).
 * BUG-35 FIX: "Forgot password?" link added to login form.
 */
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import toast from 'react-hot-toast'
import { useAuthStore } from '../../store/authStore'

interface Props {
  defaultMode?: 'login' | 'register'
}

export default function AuthModal({ defaultMode = 'register' }: Props) {
  const [mode, setMode]       = useState<'login' | 'register'>(defaultMode)
  const [email, setEmail]     = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [loading, setLoading] = useState(false)
  const { login, register }   = useAuthStore()
  const navigate              = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      if (mode === 'login') {
        await login(email, password)
        toast.success('Welcome back!')
      } else {
        await register(email, password, fullName || undefined)
        toast.success('Account created! Welcome to LeaseLens.')
      }
      navigate('/analyze')
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } }
      const msg = axiosErr?.response?.data?.detail ?? 'Something went wrong. Please try again.'
      toast.error(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="w-full">
      <div className="text-center mb-6">
        <div className="text-3xl mb-2">⚖️</div>
        <h2 className="font-display text-2xl font-bold text-slate-900">
          {mode === 'login' ? 'Welcome back' : 'Protect yourself today'}
        </h2>
        <p className="text-sm text-slate-500 mt-1">
          {mode === 'login'
            ? 'Sign in to access your analyses'
            : 'Free account · No credit card needed'}
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {mode === 'register' && (
          <div>
            <label className="block text-xs font-semibold text-slate-500
                               uppercase tracking-wider mb-1.5">
              Full Name (optional)
            </label>
            <input
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="Priya Mehta"
              className="w-full px-4 py-3 text-sm border border-slate-200 rounded-xl
                         focus:outline-none focus:ring-2 focus:ring-navy-500/30
                         focus:border-navy-400 transition-all"
            />
          </div>
        )}

        <div>
          <label className="block text-xs font-semibold text-slate-500
                             uppercase tracking-wider mb-1.5">
            Email
          </label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="priya@example.com"
            required
            className="w-full px-4 py-3 text-sm border border-slate-200 rounded-xl
                       focus:outline-none focus:ring-2 focus:ring-navy-500/30
                       focus:border-navy-400 transition-all"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-500
                             uppercase tracking-wider mb-1.5">
            Password
          </label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder={
              mode === 'register'
                ? 'Min 8 chars, 1 uppercase, 1 number'
                : 'Your password'
            }
            required
            className="w-full px-4 py-3 text-sm border border-slate-200 rounded-xl
                       focus:outline-none focus:ring-2 focus:ring-navy-500/30
                       focus:border-navy-400 transition-all"
          />
          {/* BUG-35 FIX: Forgot password link on login mode */}
          {mode === 'login' && (
            <div className="flex justify-end mt-1.5">
              <Link to="/forgot-password"
                className="text-xs text-slate-400 hover:text-navy-600 transition-colors">
                Forgot password?
              </Link>
            </div>
          )}
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full py-3.5 bg-navy-500 text-white rounded-xl font-semibold
                     text-sm hover:bg-navy-600 active:scale-[0.98] transition-all
                     disabled:opacity-50 disabled:cursor-not-allowed
                     shadow-lg shadow-navy-500/20"
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <span className="w-4 h-4 border-2 border-white/30 border-t-white
                               rounded-full animate-spin" />
              {mode === 'login' ? 'Signing in…' : 'Creating account…'}
            </span>
          ) : mode === 'login' ? (
            'Sign In'
          ) : (
            'Create Free Account'
          )}
        </button>
      </form>

      <div className="mt-5 text-center">
        <button
          onClick={() => setMode(mode === 'login' ? 'register' : 'login')}
          className="text-sm text-slate-500 hover:text-navy-600 transition-colors"
        >
          {mode === 'login'
            ? "Don't have an account? Sign up free →"
            : 'Already have an account? Sign in →'}
        </button>
      </div>
    </div>
  )
}
