/**
 * Analysis state store.
 * BUG-29 FIX: current result is persisted to localStorage so a page refresh
 *             doesn't wipe the result before BUG-24 URL fetch kicks in.
 *             This is safe because the persisted data is the analysis result
 *             (not auth credentials). The full result is also fetchable by ID.
 */
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface LeaseSummary {
  property_address:  string | null
  landlord_name:     string | null
  tenant_name:       string | null
  lease_start:       string | null
  lease_end:         string | null
  monthly_rent:      number | null
  currency:          string
  security_deposit:  number | null
  lease_type:        'RESIDENTIAL' | 'COMMERCIAL' | 'UNKNOWN'
}

export interface RiskSummary {
  critical_count:  number
  high_count:      number
  medium_count:    number
  low_count:       number
  missing_clauses: string[]
  illegal_clauses: string[]
}

export interface Clause {
  clause_id:              string
  clause_type:            string
  verbatim_excerpt:       string
  risk_level:             'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'SAFE'
  legal_status:           'ILLEGAL' | 'SUSPECT' | 'MISSING' | 'UNFAIR' | 'STANDARD' | 'FAVORABLE_TO_TENANT'
  plain_english:          string
  legal_citation:         string
  negotiation_suggestion: string
  fairness_weight:        number
  is_actionable:          boolean
}

export interface NegotiationPriority {
  priority:                          number
  clause_id:                         string
  reason:                            string
  suggested_response_letter_snippet: string
}

export interface AnalysisResult {
  analysis_id:                     string
  jurisdiction:                    string
  lease_summary:                   LeaseSummary
  fairness_score:                  number
  risk_summary:                    RiskSummary
  clauses:                         Clause[]
  top_3_negotiation_priorities:    NegotiationPriority[]
  counter_proposal_letter:         string
  legal_disclaimer:                string
  processing_time_ms:              number | null
  created_at:                      string | null
}

export interface HistoryItem {
  id:                string
  jurisdiction:      string
  fairness_score:    number | null
  original_filename: string | null
  lease_type:        string
  created_at:        string | null
}

interface AnalysisState {
  current:        AnalysisResult | null
  history:        HistoryItem[]
  isAnalyzing:    boolean
  analysisStage:  string
  error:          string | null
  setCurrent:     (result: AnalysisResult) => void
  setAnalyzing:   (v: boolean, stage?: string) => void
  setError:       (e: string | null) => void
  setHistory:     (items: HistoryItem[]) => void
  clearCurrent:   () => void
}

export const useAnalysisStore = create<AnalysisState>()(
  persist(
    (set) => ({
      current:       null,
      history:       [],
      isAnalyzing:   false,
      analysisStage: '',
      error:         null,

      setCurrent:   (result) => set({ current: result, error: null }),
      setAnalyzing: (v, stage = '') => set({ isAnalyzing: v, analysisStage: stage }),
      setError:     (e) => set({ error: e, isAnalyzing: false }),
      setHistory:   (items) => set({ history: items }),
      clearCurrent: () => set({ current: null, error: null }),
    }),
    {
      name: 'll_analysis_v1',
      // BUG-29 FIX: persist current result — survives refresh
      // Do NOT persist: isAnalyzing, analysisStage, error (transient)
      partialize: (state) => ({
        current: state.current,
        // history is re-fetched on mount — no need to persist it
      }),
    }
  )
)
