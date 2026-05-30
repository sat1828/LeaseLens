/**
 * Analyze page.
 * BUG-36 FIX: Shows upgrade success banner when redirected from Stripe
 *             via ?upgraded=true query param.
 */
import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useSearchParams } from 'react-router-dom'
import UploadPanel from '../components/upload/LeaseDropzone'
import { useAnalysis } from '../hooks/useAnalysis'
import { useAnalysisStore } from '../store/analysisStore'
import { useAuthStore } from '../store/authStore'

const STAGE_ICONS  = ['📄', '⚖️', '🔍', '📊', '✍️', '✅']
const STAGE_KEYS   = ['Reading', 'Checking', 'Identifying', 'Calculating', 'Writing', 'Finalising']

export default function Analyze() {
  const [jurisdiction, setJurisdiction] = useState('Bengaluru, Karnataka, India')
  const { runAnalysis }                  = useAnalysis()
  const { isAnalyzing, analysisStage, error } = useAnalysisStore()
  const { user }                         = useAuthStore()

  // BUG-36 FIX: detect Stripe redirect success
  const [searchParams, setSearchParams]  = useSearchParams()
  const justUpgraded                     = searchParams.get('upgraded') === 'true'
  const upgradedPlan                     = searchParams.get('plan') ?? 'Pro'

  const dismissUpgrade = () => {
    searchParams.delete('upgraded')
    searchParams.delete('plan')
    setSearchParams(searchParams)
  }

  const stageIndex = Math.max(
    0,
    STAGE_KEYS.findIndex((s) => analysisStage.startsWith(s))
  )

  if (isAnalyzing) {
    return (
      <div className="min-h-[70vh] flex items-center justify-center px-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="max-w-md w-full text-center"
        >
          {/* Spinner */}
          <div className="relative w-24 h-24 mx-auto mb-8">
            <div className="absolute inset-0 rounded-full border-4 border-slate-100" />
            <div className="absolute inset-0 rounded-full border-4 border-t-navy-500
                            border-r-navy-500 border-b-transparent border-l-transparent
                            animate-spin" />
            <div className="absolute inset-0 flex items-center justify-center text-3xl">
              ⚖️
            </div>
          </div>

          <h2 className="font-display text-2xl font-bold text-slate-900 mb-2">
            Analysing your lease
          </h2>
          <p className="text-sm text-slate-500 mb-8">
            {analysisStage || 'Reading your lease document…'}
          </p>

          {/* Stage icons */}
          <div className="flex justify-center gap-2 mb-6">
            {STAGE_ICONS.map((icon, i) => (
              <motion.div
                key={i}
                animate={{
                  scale:   i === stageIndex ? 1.3 : 1,
                  opacity: i <= stageIndex ? 1 : 0.25,
                }}
                className="text-xl"
              >
                {icon}
              </motion.div>
            ))}
          </div>

          {/* Progress dots */}
          <div className="flex gap-1.5 justify-center">
            {Array.from({ length: 6 }).map((_, i) => (
              <motion.div
                key={i}
                className="h-1 rounded-full bg-navy-500"
                animate={{
                  width:   i <= stageIndex ? 28 : 8,
                  opacity: i <= stageIndex ? 1 : 0.2,
                }}
                transition={{ duration: 0.4 }}
              />
            ))}
          </div>

          <p className="text-xs text-slate-400 mt-6">
            Usually takes 15–30 seconds · Please keep this tab open
          </p>
        </motion.div>
      </div>
    )
  }

  return (
    <div className="min-h-[70vh] max-w-2xl mx-auto px-4 sm:px-6 py-12">

      {/* BUG-36 FIX: Stripe success banner */}
      <AnimatePresence>
        {justUpgraded && (
          <motion.div
            initial={{ opacity: 0, y: -12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -12 }}
            className="mb-6 p-4 bg-green-50 border border-green-200 rounded-xl
                       flex items-start justify-between gap-3"
          >
            <div className="flex items-start gap-3">
              <span className="text-xl flex-shrink-0">🎉</span>
              <div>
                <p className="text-sm font-semibold text-green-800">
                  Welcome to {upgradedPlan}!
                </p>
                <p className="text-xs text-green-700 mt-0.5">
                  Unlimited analyses are now active on your account.
                </p>
              </div>
            </div>
            <button
              onClick={dismissUpgrade}
              className="text-green-500 hover:text-green-700 transition-colors
                         flex-shrink-0 text-lg leading-none"
              aria-label="Dismiss"
            >
              ×
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-8"
      >
        <h1 className="font-display text-3xl font-bold text-slate-900 mb-2">
          Analyze Your Lease
        </h1>
        <p className="text-sm text-slate-500">
          Upload your rental agreement or paste the text.{' '}
          {user && (
            <span className="text-navy-600 font-medium">
              {user.plan === 'FREE'
                ? `${Math.max(0, 1 - user.monthly_analysis_count)} free analysis remaining this month`
                : 'Unlimited analyses'}
            </span>
          )}
        </p>
      </motion.div>

      {error && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl
                     text-sm text-red-700 flex items-start gap-2"
        >
          <span className="flex-shrink-0">⚠️</span>
          <span>{error}</span>
        </motion.div>
      )}

      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="bg-white border border-slate-100 rounded-2xl shadow-sm p-6"
      >
        <UploadPanel
          jurisdiction={jurisdiction}
          onJurisdictionChange={setJurisdiction}
          onSubmit={(input: File | string) => runAnalysis(input, jurisdiction)}
          disabled={isAnalyzing}
        />
      </motion.div>

      {/* How it works */}
      <div className="mt-10 grid grid-cols-3 gap-4 text-center">
        {[
          { step: '1', title: 'Upload or paste', desc: 'PDF or plain text' },
          { step: '2', title: 'AI audits clauses', desc: 'Against tenancy law' },
          { step: '3', title: 'Get your report',  desc: 'Score + letter' },
        ].map((item) => (
          <div key={item.step}>
            <div className="w-8 h-8 rounded-full bg-navy-500 text-white text-xs font-bold
                            flex items-center justify-center mx-auto mb-2">
              {item.step}
            </div>
            <div className="text-xs font-semibold text-slate-700">{item.title}</div>
            <div className="text-[10px] text-slate-400">{item.desc}</div>
          </div>
        ))}
      </div>
    </div>
  )
}
