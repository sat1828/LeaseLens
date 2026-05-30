import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import toast from 'react-hot-toast'
import { RiskBadge, StatusBadge } from './RiskBadge'
import type { Clause } from '../../store/analysisStore'

interface Props {
  clause: Clause
  index: number
}

const CLAUSE_LABELS: Record<string, string> = {
  RENT_AMOUNT_AND_PAYMENT: 'Rent & Payment',
  RENT_ESCALATION: 'Rent Escalation',
  SECURITY_DEPOSIT: 'Security Deposit',
  LEASE_DURATION: 'Lease Duration',
  NOTICE_PERIOD: 'Notice Period',
  MAINTENANCE_OBLIGATIONS: 'Maintenance',
  EVICTION_GROUNDS: 'Eviction Grounds',
  ENTRY_AND_PRIVACY: 'Entry & Privacy',
  UTILITY_AND_SERVICES: 'Utilities',
  SUBLETTING: 'Subletting',
  LOCK_IN_PERIOD: 'Lock-in Period',
  ILLEGAL_CLAUSES: 'Illegal Clause',
  DISPUTE_RESOLUTION: 'Dispute Resolution',
  PENALTY_CLAUSES: 'Penalties',
  MODIFICATION_RIGHTS: 'Modification Rights',
  REGISTRATION_COMPLIANCE: 'Registration',
}

export default function ClauseCard({ clause, index }: Props) {
  const [open, setOpen] = useState(false)
  const [copied, setCopied] = useState<'suggestion' | null>(null)

  const copy = (text: string, type: 'suggestion') => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(type)
      toast.success('Copied to clipboard')
      setTimeout(() => setCopied(null), 2000)
    })
  }

  const borderColors: Record<string, string> = {
    CRITICAL: 'border-l-red-500',
    HIGH: 'border-l-orange-500',
    MEDIUM: 'border-l-amber-500',
    LOW: 'border-l-green-500',
    SAFE: 'border-l-blue-400',
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.04, duration: 0.3 }}
      className={`bg-white border border-slate-100 border-l-4 ${borderColors[clause.risk_level] || 'border-l-slate-300'} rounded-xl overflow-hidden shadow-sm hover:shadow-md transition-shadow`}
    >
      {/* Header — always visible */}
      <button
        onClick={() => setOpen(!open)}
        className="w-full text-left p-4 flex items-start gap-3 hover:bg-slate-50/50 transition-colors"
      >
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-1.5 mb-2">
            <RiskBadge level={clause.risk_level} />
            <StatusBadge status={clause.legal_status} />
            <span className="text-[10px] text-slate-400 font-mono bg-slate-100 px-1.5 py-0.5 rounded">
              {CLAUSE_LABELS[clause.clause_type] || clause.clause_type.replace(/_/g, ' ')}
            </span>
          </div>
          <p className="text-sm text-slate-700 leading-relaxed line-clamp-2">
            {clause.plain_english}
          </p>
        </div>
        <motion.span
          animate={{ rotate: open ? 180 : 0 }}
          transition={{ duration: 0.2 }}
          className="text-slate-400 flex-shrink-0 mt-0.5 text-xs"
        >
          ▼
        </motion.span>
      </button>

      {/* Expandable details */}
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25, ease: 'easeInOut' }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-4 pt-1 border-t border-slate-100 space-y-4 bg-slate-50/30">

              {/* Verbatim excerpt */}
              {clause.verbatim_excerpt && (
                <div>
                  <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1.5">
                    Exact Clause Text
                  </div>
                  <blockquote className="text-xs text-slate-600 italic leading-relaxed px-3 py-2.5 bg-white border border-slate-200 rounded-lg border-l-2 border-l-slate-400">
                    "{clause.verbatim_excerpt}"
                  </blockquote>
                </div>
              )}

              {/* Legal citation */}
              {clause.legal_citation && (
                <div className="flex items-start gap-2">
                  <span className="text-base">⚖️</span>
                  <div>
                    <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-0.5">
                      Legal Basis
                    </div>
                    <span className="text-xs text-blue-700 font-medium bg-blue-50 px-2 py-1 rounded-md border border-blue-100">
                      {clause.legal_citation}
                    </span>
                  </div>
                </div>
              )}

              {/* Negotiation suggestion */}
              {clause.negotiation_suggestion && (
                <div>
                  <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1.5">
                    Request This Instead
                  </div>
                  <div className="flex items-start gap-2 p-3 bg-emerald-50 border border-emerald-200 rounded-lg">
                    <p className="flex-1 text-xs text-emerald-800 leading-relaxed">
                      {clause.negotiation_suggestion}
                    </p>
                    <button
                      onClick={() => copy(clause.negotiation_suggestion, 'suggestion')}
                      className="flex-shrink-0 text-[10px] font-bold px-2 py-1 bg-emerald-100 hover:bg-emerald-200 text-emerald-700 rounded-md transition-colors"
                    >
                      {copied === 'suggestion' ? '✓' : 'Copy'}
                    </button>
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}
