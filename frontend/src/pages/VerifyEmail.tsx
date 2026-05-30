import { useEffect, useState } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { api } from '../api/client'

export default function VerifyEmail() {
  const [searchParams] = useSearchParams()
  const token          = searchParams.get('token') ?? ''
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading')
  const [message, setMessage] = useState('')

  useEffect(() => {
    if (!token) { setStatus('error'); setMessage('No verification token found.'); return }
    api.verifyEmail(token)
      .then(({ data }) => { setStatus('success'); setMessage(data.message) })
      .catch((err) => {
        setStatus('error')
        setMessage(err?.response?.data?.detail ?? 'Verification failed. Please request a new link.')
      })
  }, [token])

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4">
      <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}
        className="text-center max-w-sm">
        {status === 'loading' && (
          <>
            <div className="w-10 h-10 border-2 border-navy-500 border-t-transparent
                            rounded-full animate-spin mx-auto mb-4" />
            <p className="text-sm text-slate-500">Verifying your email…</p>
          </>
        )}
        {status === 'success' && (
          <>
            <div className="text-5xl mb-4">✅</div>
            <h2 className="font-display text-2xl font-bold text-slate-900 mb-2">
              Email verified!
            </h2>
            <p className="text-sm text-slate-500 mb-6">{message}</p>
            <Link to="/analyze" className="btn-primary">Start Analyzing →</Link>
          </>
        )}
        {status === 'error' && (
          <>
            <div className="text-5xl mb-4">⚠️</div>
            <h2 className="font-display text-2xl font-bold text-slate-900 mb-2">
              Verification failed
            </h2>
            <p className="text-sm text-slate-500 mb-6">{message}</p>
            <Link to="/login" className="btn-primary">Back to Login</Link>
          </>
        )}
      </motion.div>
    </div>
  )
}
