import { useState } from 'react'
import { useSearchParams, useNavigate, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { api } from '../api/client'
import toast from 'react-hot-toast'

export default function ResetPassword() {
  const [searchParams]  = useSearchParams()
  const token           = searchParams.get('token') ?? ''
  const [password, setPassword] = useState('')
  const [confirm, setConfirm]   = useState('')
  const [loading, setLoading]   = useState(false)
  const [done, setDone]         = useState(false)
  const navigate                = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (password !== confirm) {
      toast.error('Passwords do not match.')
      return
    }
    if (!token) {
      toast.error('Invalid reset link. Please request a new one.')
      return
    }
    setLoading(true)
    try {
      await api.resetPassword(token, password)
      setDone(true)
      toast.success('Password reset! Please sign in.')
      setTimeout(() => navigate('/login'), 2000)
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } }
      toast.error(axiosErr?.response?.data?.detail ?? 'Reset failed. Request a new link.')
    } finally {
      setLoading(false)
    }
  }

  if (!token) {
    return (
      <div className="min-h-[80vh] flex items-center justify-center px-4 text-center">
        <div>
          <div className="text-4xl mb-3">🔗</div>
          <h2 className="font-display text-xl font-bold text-slate-900 mb-2">
            Invalid reset link
          </h2>
          <p className="text-sm text-slate-500 mb-4">
            This link is invalid or has expired.
          </p>
          <Link to="/forgot-password" className="btn-primary">
            Request New Link
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md bg-white border border-slate-100 rounded-2xl shadow-sm p-8">
        <h2 className="font-display text-2xl font-bold text-slate-900 mb-1">
          Set new password
        </h2>
        <p className="text-sm text-slate-500 mb-6">
          Choose a strong password. Min 8 characters, 1 uppercase, 1 number.
        </p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)}
            placeholder="New password" required
            className="w-full px-4 py-3 text-sm border border-slate-200 rounded-xl
                       focus:outline-none focus:ring-2 focus:ring-navy-500/30 transition-all"
          />
          <input type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)}
            placeholder="Confirm new password" required
            className="w-full px-4 py-3 text-sm border border-slate-200 rounded-xl
                       focus:outline-none focus:ring-2 focus:ring-navy-500/30 transition-all"
          />
          <button type="submit" disabled={loading || done}
            className="w-full py-3.5 bg-navy-500 text-white rounded-xl font-semibold
                       text-sm hover:bg-navy-600 transition-all disabled:opacity-50">
            {done ? '✓ Password reset!' : loading ? 'Resetting…' : 'Reset Password'}
          </button>
        </form>
      </motion.div>
    </div>
  )
}
