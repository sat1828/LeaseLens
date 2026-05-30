/**
 * Analysis result page.
 * BUG-24 FIX: Route is now /result/:analysisId — survives page refresh.
 *   On mount: if result not in memory, fetches from API by ID.
 * BUG-26 FIX: All .map() calls are null-safe with ?? [] fallbacks.
 */
import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import toast from 'react-hot-toast'
import { useAnalysisStore, type Clause } from '../store/analysisStore'
import { api } from '../api/client'
import FairnessGauge from '../components/analysis/FairnessGauge'
import RiskSummaryBar from '../components/analysis/RiskSummaryBar'
import ClauseCard from '../components/analysis/ClauseCard'
import CounterProposalViewer from '../components/letter/CounterProposalViewer'

type FilterType = 'ALL' | 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'SAFE'
type TabType = 'overview' | 'clauses' | 'missing' | 'letter'

export default function Result() {
  // BUG-24 FIX: Read analysisId from URL params
  const { analysisId } = useParams<{ analysisId: string }>()
  const { current, setCurrent, clearCurrent } = useAnalysisStore()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState<TabType>('overview')
  const [filter, setFilter] = useState<FilterType>('ALL')

  // BUG-24 FIX: Fetch from API if result not in memory OR if it's a different analysis
  useEffect(() => {
    if (!analysisId) return

    const needsFetch =
      !current ||
      (current.analysis_id !== analysisId)

    if (needsFetch) {
      setLoading(true)
      api.getAnalysis(analysisId)
        .then(({ data }) => setCurrent(data))
        .catch(() => {
          toast.error('Could not load this analysis. It may have expired (90-day limit).')
          navigate('/history')
        })
        .finally(() => setLoading(false))
    }
  }, [analysisId]) // eslint-disable-line react-hooks/exhaustive-deps

  if (loading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="text-center">
          <div className="w-10 h-10 border-2 border-navy-500 border-t-transparent
                          rounded-full animate-spin mx-auto mb-4" />
          <p className="text-sm text-slate-500">Loading analysis…</p>
        </div>
      </div>
    )
  }

  if (!current) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center gap-4
                      text-center px-4">
        <div className="text-5xl">📭</div>
        <h2 className="font-display text-xl font-bold text-slate-900">
          Analysis not found
        </h2>
        <p className="text-sm text-slate-500">
          This analysis may have expired or been deleted.
        </p>
        <button onClick={() => navigate('/analyze')} className="btn-primary">
          Analyze a Lease →
        </button>
      </div>
    )
  }

  // BUG-26 FIX: null-safe destructuring with fallbacks for every array/object field
  const leaseSummary = current.lease_summary ?? {
    monthly_rent: null, security_deposit: null, property_address: null,
    landlord_name: null, tenant_name: null, lease_start: null, lease_end: null,
    currency: 'INR', lease_type: 'UNKNOWN',
  }
  const riskSummary = current.risk_summary ?? {
    critical_count: 0, high_count: 0, medium_count: 0, low_count: 0,
    missing_clauses: [], illegal_clauses: [],
  }
  const clauses: Clause[]           = current.clauses ?? []
  const priorities                   = current.top_3_negotiation_priorities ?? []
  const missingClauses: string[]     = riskSummary.missing_clauses ?? []
  const illegalClauses: string[]     = riskSummary.illegal_clauses ?? []

  const filteredClauses = filter === 'ALL'
    ? clauses
    : clauses.filter((c) => c.risk_level === filter)

  const tabs: { id: TabType; label: string; count?: number }[] = [
    { id: 'overview', label: '📋 Overview' },
    { id: 'clauses',  label: '⚠️ Clauses',  count: clauses.length },
    { id: 'missing',  label: '🟣 Missing',  count: missingClauses.length },
    { id: 'letter',   label: '✉️ Letter' },
  ]

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-8 space-y-5">

      {/* Score header */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white border border-slate-100 rounded-2xl shadow-sm p-5"
      >
        <div className="flex flex-col sm:flex-row items-center gap-6">
          <FairnessGauge score={current.fairness_score} size={140} />

          <div className="flex-1 w-full">
            {leaseSummary.property_address && (
              <div className="text-xs text-slate-500 mb-3 flex items-center gap-1">
                📍 {leaseSummary.property_address}
              </div>
            )}
            <div className="grid grid-cols-2 gap-2 mb-4">
              {leaseSummary.monthly_rent != null && (
                <div className="bg-slate-50 rounded-lg p-2.5">
                  <div className="text-[10px] text-slate-400 uppercase tracking-wide">
                    Monthly Rent
                  </div>
                  <div className="font-bold text-slate-900 text-base">
                    ₹{leaseSummary.monthly_rent.toLocaleString('en-IN')}
                  </div>
                </div>
              )}
              {leaseSummary.security_deposit != null && (
                <div className={`rounded-lg p-2.5 ${
                  leaseSummary.monthly_rent != null &&
                  leaseSummary.security_deposit > leaseSummary.monthly_rent * 2
                    ? 'bg-red-50 border border-red-200'
                    : 'bg-slate-50'
                }`}>
                  <div className="text-[10px] text-slate-400 uppercase tracking-wide flex items-center gap-1">
                    Security Deposit
                    {leaseSummary.monthly_rent != null &&
                     leaseSummary.security_deposit > leaseSummary.monthly_rent * 2 && (
                      <span className="text-red-500 font-bold">⚠ Over limit</span>
                    )}
                  </div>
                  <div className={`font-bold text-base ${
                    leaseSummary.monthly_rent != null &&
                    leaseSummary.security_deposit > leaseSummary.monthly_rent * 2
                      ? 'text-red-700'
                      : 'text-slate-900'
                  }`}>
                    ₹{leaseSummary.security_deposit.toLocaleString('en-IN')}
                  </div>
                  {leaseSummary.monthly_rent != null &&
                   leaseSummary.security_deposit > leaseSummary.monthly_rent * 2 && (
                    <div className="text-[10px] text-red-600 mt-0.5">
                      Legal max: ₹{(leaseSummary.monthly_rent * 2).toLocaleString('en-IN')}
                    </div>
                  )}
                </div>
              )}
            </div>
            <RiskSummaryBar summary={riskSummary} />
          </div>
        </div>
      </motion.div>

      {/* Tabs */}
      <div className="bg-slate-100 rounded-xl p-1 flex gap-1">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex-1 py-2 px-2 rounded-lg text-xs font-semibold transition-all
                        flex items-center justify-center gap-1.5 ${
              activeTab === tab.id
                ? 'bg-white text-slate-900 shadow-sm'
                : 'text-slate-500 hover:text-slate-700'
            }`}
          >
            {tab.label}
            {tab.count != null && tab.count > 0 && (
              <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-bold ${
                activeTab === tab.id
                  ? 'bg-navy-100 text-navy-700'
                  : 'bg-slate-200 text-slate-500'
              }`}>
                {tab.count}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <motion.div
        key={activeTab}
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2 }}
      >

        {/* ── Overview ─────────────────────────────────────────────────────── */}
        {activeTab === 'overview' && (
          <div className="space-y-4">
            {priorities.length > 0 && (
              <div>
                <h3 className="font-semibold text-sm text-slate-900 mb-3 uppercase tracking-wide">
                  🎯 Top {priorities.length} Priorities Before You Sign
                </h3>
                <div className="space-y-3">
                  {priorities.map((p, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, x: -12 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.08 }}
                      className="bg-white border border-slate-100 rounded-xl p-4 shadow-sm"
                    >
                      <div className="flex items-start gap-3">
                        <div className={`w-6 h-6 rounded-full flex items-center justify-center
                                         text-white text-xs font-bold flex-shrink-0 ${
                          ['bg-red-500', 'bg-orange-500', 'bg-amber-500'][i] || 'bg-slate-400'
                        }`}>
                          {p.priority}
                        </div>
                        <div>
                          <p className="text-sm font-semibold text-slate-900 mb-1">
                            {p.reason}
                          </p>
                          {p.suggested_response_letter_snippet && (
                            <p className="text-xs text-slate-500 italic bg-slate-50
                                          px-3 py-2 rounded-lg border border-slate-100">
                              "{p.suggested_response_letter_snippet}"
                            </p>
                          )}
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>
            )}

            {illegalClauses.length > 0 && (
              <div className="bg-red-50 border border-red-200 rounded-xl p-4">
                <h4 className="font-bold text-red-800 text-sm mb-2">
                  ⛔ These clauses are illegal — void and unenforceable
                </h4>
                <p className="text-xs text-red-700 mb-3 leading-relaxed">
                  The following clauses violate Indian tenancy law and are void ab initio.
                  You are not legally required to comply with them even if you signed.
                </p>
                <div className="flex flex-wrap gap-2">
                  {illegalClauses.map((c) => (
                    <span key={c}
                      className="text-xs bg-red-100 text-red-800 border border-red-300
                                 px-2 py-1 rounded-md font-mono">
                      {c.replace(/_/g, ' ')}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <button
              onClick={() => setActiveTab('clauses')}
              className="w-full py-3 border border-slate-200 rounded-xl text-sm font-medium
                         text-slate-600 hover:bg-slate-50 transition-colors"
            >
              View all {clauses.length} clause analyses →
            </button>
          </div>
        )}

        {/* ── Clauses ──────────────────────────────────────────────────────── */}
        {activeTab === 'clauses' && (
          <div>
            <div className="flex gap-1.5 flex-wrap mb-4">
              {(['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'SAFE'] as FilterType[]).map((f) => {
                const count = f === 'ALL'
                  ? clauses.length
                  : clauses.filter((c) => c.risk_level === f).length
                return (
                  <button
                    key={f}
                    onClick={() => setFilter(f)}
                    disabled={count === 0 && f !== 'ALL'}
                    className={`text-xs px-3 py-1.5 rounded-full font-semibold border
                                transition-all ${
                      filter === f
                        ? 'bg-navy-500 text-white border-navy-500'
                        : count === 0
                        ? 'bg-slate-50 text-slate-300 border-slate-100 cursor-not-allowed'
                        : 'bg-white text-slate-600 border-slate-200 hover:border-slate-300'
                    }`}
                  >
                    {f}{count > 0 && <span className="ml-0.5 opacity-70">({count})</span>}
                  </button>
                )
              })}
            </div>
            <div className="space-y-2">
              {filteredClauses.length === 0 ? (
                <div className="text-center py-12 text-slate-400 text-sm">
                  No clauses at this risk level.
                </div>
              ) : (
                filteredClauses.map((clause, i) => (
                  <ClauseCard key={clause.clause_id} clause={clause} index={i} />
                ))
              )}
            </div>
          </div>
        )}

        {/* ── Missing clauses ───────────────────────────────────────────────── */}
        {activeTab === 'missing' && (
          <div>
            {missingClauses.length === 0 ? (
              <div className="text-center py-16">
                <div className="text-4xl mb-3">✅</div>
                <p className="font-semibold text-green-700">
                  No mandatory clauses are missing.
                </p>
                <p className="text-sm text-slate-500 mt-1">
                  All legally required protections are present in this agreement.
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                <p className="text-sm text-slate-600 bg-violet-50 border border-violet-200
                               rounded-xl p-3">
                  <strong>These clauses are absent from your agreement.</strong>{' '}
                  Their absence may leave you legally unprotected. Demand they be added
                  before signing.
                </p>
                {missingClauses.map((clause, i) => (
                  <motion.div
                    key={clause}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.06 }}
                    className="bg-white border-l-4 border-l-violet-500 border border-slate-100
                               rounded-xl p-4 shadow-sm"
                  >
                    <div className="flex items-center gap-2">
                      <span className="text-violet-500 text-sm">🟣</span>
                      <span className="font-semibold text-sm text-slate-900">
                        {clause.replace(/_/g, ' ')}
                      </span>
                      <span className="ml-auto text-[10px] bg-violet-100 text-violet-700
                                       px-2 py-0.5 rounded-md font-bold">
                        MISSING
                      </span>
                    </div>
                    <p className="text-xs text-slate-500 mt-1.5 ml-6">
                      Not present in this agreement. Add to counter-proposal letter.
                    </p>
                  </motion.div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ── Letter ───────────────────────────────────────────────────────── */}
        {activeTab === 'letter' && (
          <div className="bg-white border border-slate-100 rounded-2xl p-5 shadow-sm">
            {current.counter_proposal_letter ? (
              <CounterProposalViewer
                letter={current.counter_proposal_letter}
                jurisdiction={current.jurisdiction}
              />
            ) : (
              <div className="text-center py-12 text-slate-400 text-sm">
                Letter not generated. Re-run the analysis.
              </div>
            )}
          </div>
        )}
      </motion.div>

      {/* Footer actions */}
      <div className="flex flex-col sm:flex-row gap-3">
        <button
          onClick={() => { clearCurrent(); navigate('/analyze') }}
          className="btn-secondary flex-1"
        >
          ← Analyze Another Lease
        </button>
        <button
          onClick={() => navigate('/history')}
          className="btn-secondary flex-1"
        >
          My History
        </button>
      </div>

      {/* Legal disclaimer */}
      <div className="text-[11px] text-slate-400 leading-relaxed bg-amber-50
                      border border-amber-100 rounded-lg p-3">
        ⚖️ {current.legal_disclaimer || 'LeaseLens provides AI-assisted analysis for informational purposes only. Not legal advice.'}
      </div>
    </div>
  )
}
