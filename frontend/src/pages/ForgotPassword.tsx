import { useState } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { api } from '../api/client'
import toast from 'react-hot-toast'

export default function ForgotPassword() {
  const [email, setEmail]   = useState('')
  const [sent, setSent]     = useState(false)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await api.forgotPassword(email)
      setSent(true)
    } catch {
      toast.error('Something went wrong. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  if (sent) {
    return (
      <div className="min-h-[80vh] flex items-center justify-center px-4">
        <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}
          className="text-center max-w-sm">
          <div className="text-5xl mb-4">📬</div>
          <h2 className="font-display text-2xl font-bold text-slate-900 mb-2">
            Check your inbox
          </h2>
          <p className="text-sm text-slate-500 mb-6">
            If <strong>{email}</strong> is registered, you'll receive a reset link
            within 5 minutes. Check your spam folder too.
          </p>
          <Link to="/login" className="btn-primary">Back to Login</Link>
        </motion.div>
      </div>
    )
  }

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md bg-white border border-slate-100 rounded-2xl shadow-sm p-8">
        <h2 className="font-display text-2xl font-bold text-slate-900 mb-1">
          Reset your password
        </h2>
        <p className="text-sm text-slate-500 mb-6">
          Enter the email address for your account and we'll send a reset link.
        </p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)}
            placeholder="priya@example.com" required
            className="w-full px-4 py-3 text-sm border border-slate-200 rounded-xl
                       focus:outline-none focus:ring-2 focus:ring-navy-500/30 transition-all"
          />
          <button type="submit" disabled={loading}
            className="w-full py-3.5 bg-navy-500 text-white rounded-xl font-semibold
                       text-sm hover:bg-navy-600 transition-all disabled:opacity-50">
            {loading ? 'Sending…' : 'Send Reset Link'}
          </button>
        </form>
        <div className="mt-4 text-center">
          <Link to="/login" className="text-sm text-slate-400 hover:text-navy-600">
            Back to login
          </Link>
        </div>
      </motion.div>
    </div>
  )
}
