import { motion } from 'framer-motion'
import type { RiskSummary } from '../../store/analysisStore'

interface Props {
  summary: RiskSummary
}

export default function RiskSummaryBar({ summary }: Props) {
  const items = [
    { label: 'Critical', count: summary.critical_count, color: 'bg-red-500', text: 'text-red-700', bg: 'bg-red-50', border: 'border-red-200', icon: '⚠' },
    { label: 'High', count: summary.high_count, color: 'bg-orange-500', text: 'text-orange-700', bg: 'bg-orange-50', border: 'border-orange-200', icon: '🔴' },
    { label: 'Medium', count: summary.medium_count, color: 'bg-amber-500', text: 'text-amber-700', bg: 'bg-amber-50', border: 'border-amber-200', icon: '🟡' },
    { label: 'Low', count: summary.low_count, color: 'bg-green-500', text: 'text-green-700', bg: 'bg-green-50', border: 'border-green-200', icon: '🟢' },
  ]

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-4 gap-2">
        {items.map((item, i) => (
          <motion.div
            key={item.label}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: i * 0.08 }}
            className={`${item.bg} border ${item.border} rounded-xl p-3 text-center`}
          >
            <div className={`text-2xl font-black font-display ${item.text}`}>
              {item.count}
            </div>
            <div className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold mt-0.5">
              {item.label}
            </div>
          </motion.div>
        ))}
      </div>

      {summary.missing_clauses.length > 0 && (
        <div className="bg-violet-50 border border-violet-200 rounded-xl p-3">
          <div className="flex items-center gap-2 mb-1.5">
            <span className="text-sm">🟣</span>
            <span className="text-xs font-bold text-violet-800 uppercase tracking-wide">
              {summary.missing_clauses.length} Mandatory Clause{summary.missing_clauses.length > 1 ? 's' : ''} Missing
            </span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {summary.missing_clauses.map((c) => (
              <span key={c} className="text-[10px] bg-violet-100 text-violet-700 border border-violet-200 px-2 py-0.5 rounded-md font-mono">
                {c.replace(/_/g, ' ')}
              </span>
            ))}
          </div>
        </div>
      )}

      {summary.illegal_clauses.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-3">
          <div className="flex items-center gap-2 mb-1.5">
            <span className="text-sm">⛔</span>
            <span className="text-xs font-bold text-red-800 uppercase tracking-wide">
              {summary.illegal_clauses.length} Illegal Clause{summary.illegal_clauses.length > 1 ? 's' : ''} — Unenforceable
            </span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {summary.illegal_clauses.map((c) => (
              <span key={c} className="text-[10px] bg-red-100 text-red-700 border border-red-200 px-2 py-0.5 rounded-md font-mono">
                {c.replace(/_/g, ' ')}
              </span>
            ))}
          </div>
          <p className="text-[10px] text-red-600 mt-2">
            These clauses violate Indian tenancy law. You are legally not required to comply with them.
          </p>
        </div>
      )}
    </div>
  )
}
