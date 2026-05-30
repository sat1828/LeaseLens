/**
 * Analysis history page.
 * BUG-31 FIX: Typed as HistoryItem[] instead of any[].
 * BUG-32 FIX: scoreColor() null-safe for undefined/null fairness_score.
 * BUG-33 FIX: Delete button shows loading state, disabled during operation.
 * BUG-24 FIX: navigates to /result/:id, not openAnalysis fetch.
 */
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { format } from 'date-fns'
import { api } from '../api/client'
import type { HistoryItem } from '../store/analysisStore'  // BUG-31 FIX: typed import
import toast from 'react-hot-toast'

// BUG-32 FIX: null-safe — never crashes on null/undefined score
function scoreColor(score: number | null | undefined): string {
  if (score == null)  return 'text-slate-400 bg-slate-50 border-slate-200'
  if (score >= 80)    return 'text-green-700 bg-green-50 border-green-200'
  if (score >= 60)    return 'text-lime-700 bg-lime-50 border-lime-200'
  if (score >= 40)    return 'text-amber-700 bg-amber-50 border-amber-200'
  return 'text-red-700 bg-red-50 border-red-200'
}

function scoreLabel(score: number | null | undefined): string {
  if (score == null) return '?'
  return String(score)
}

export default function History() {
  // BUG-31 FIX: properly typed — no more any[]
  const [items, setItems]       = useState<HistoryItem[]>([])
  const [loading, setLoading]   = useState(true)
  // BUG-33 FIX: track which item is being deleted
  const [deletingId, setDeletingId] = useState<string | null>(null)
  const navigate = useNavigate()

  useEffect(() => {
    api.getHistory()
      .then(({ data }) => setItems(data.items ?? []))
      .catch(() => toast.error('Failed to load history. Please refresh.'))
      .finally(() => setLoading(false))
  }, [])

  // BUG-24 FIX: navigate directly to URL — no fetch needed here
  const openAnalysis = (id: string) => {
    navigate(`/result/${id}`)
  }

  // BUG-33 FIX: loading state + disabled guard on rapid double-click
  const deleteItem = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation()
    if (deletingId) return                           // already deleting something
    if (!confirm('Permanently delete this analysis?')) return
    setDeletingId(id)
    try {
      await api.deleteAnalysis(id)
      setItems(prev => prev.filter(i => i.id !== id))
      toast.success('Analysis deleted')
    } catch {
      toast.error('Delete failed. Please try again.')
    } finally {
      setDeletingId(null)
    }
  }

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-10">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <h1 className="font-display text-2xl font-bold text-slate-900">My Analyses</h1>
        <p className="text-sm text-slate-500 mt-1">
          Analyses are stored for 90 days, then automatically deleted for your privacy.
        </p>
      </motion.div>

      {loading ? (
        <div className="text-center py-16">
          <div className="w-8 h-8 border-2 border-navy-500 border-t-transparent
                          rounded-full animate-spin mx-auto mb-3" />
          <p className="text-sm text-slate-400">Loading…</p>
        </div>
      ) : items.length === 0 ? (
        <div className="text-center py-20">
          <div className="text-4xl mb-3">📭</div>
          <h3 className="font-semibold text-slate-700 mb-1">No analyses yet</h3>
          <p className="text-sm text-slate-500 mb-6">
            Analyse your first lease to protect yourself.
          </p>
          <button onClick={() => navigate('/analyze')} className="btn-primary">
            Analyze a Lease →
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {items.map((item, i) => (
            <motion.div
              key={item.id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              onClick={() => openAnalysis(item.id)}
              className="bg-white border border-slate-100 rounded-xl p-4 cursor-pointer
                         hover:shadow-md hover:-translate-y-0.5 transition-all flex items-center gap-4"
            >
              {/* Score badge — BUG-32 FIX: null-safe */}
              <div className={`w-12 h-12 rounded-xl flex items-center justify-center
                               font-display font-black text-lg border flex-shrink-0
                               ${scoreColor(item.fairness_score)}`}>
                {scoreLabel(item.fairness_score)}
              </div>

              <div className="flex-1 min-w-0">
                <div className="font-medium text-sm text-slate-900 truncate">
                  {item.original_filename || 'Unnamed lease'}
                </div>
                <div className="text-xs text-slate-400 mt-0.5">
                  {item.jurisdiction} · {item.lease_type}
                  {item.created_at && (
                    <> · {format(new Date(item.created_at), 'd MMM yyyy')}</>
                  )}
                </div>
              </div>

              {/* BUG-33 FIX: loading state, disabled during delete */}
              <button
                onClick={(e) => deleteItem(item.id, e)}
                disabled={!!deletingId}
                className="flex-shrink-0 w-8 h-8 flex items-center justify-center
                           text-slate-300 hover:text-red-500 transition-colors
                           disabled:opacity-30 disabled:cursor-not-allowed rounded-lg
                           hover:bg-red-50"
                title="Delete analysis"
              >
                {deletingId === item.id ? (
                  <span className="text-xs animate-spin inline-block">⟳</span>
                ) : (
                  <span className="text-sm">🗑</span>
                )}
              </button>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  )
}
