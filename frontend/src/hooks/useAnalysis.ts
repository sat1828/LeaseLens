/**
 * Analysis hook.
 * BUG-24 FIX: navigate to /result/:analysisId (URL-persistent).
 * BUG-30 FIX: Stage timer clears itself when all stages shown.
 */
import { useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { api } from '../api/client'
import { useAnalysisStore } from '../store/analysisStore'

const STAGES = [
  'Reading your lease document…',
  'Checking against Indian tenancy law…',
  'Identifying risks and red flags…',
  'Calculating your fairness score…',
  'Writing your counter-proposal letter…',
  'Finalising analysis…',
]

export function useAnalysis() {
  const { setAnalyzing, setCurrent, setError } = useAnalysisStore()
  const navigate = useNavigate()

  const runAnalysis = useCallback(
    async (input: File | string, jurisdiction: string) => {
      setAnalyzing(true, STAGES[0])
      setError(null)

      let stageIdx = 0

      // BUG-30 FIX: timer stops itself when all stages are shown
      const stageTimer = setInterval(() => {
        stageIdx += 1
        if (stageIdx >= STAGES.length) {
          clearInterval(stageTimer)
          return
        }
        setAnalyzing(true, STAGES[stageIdx])
      }, 5000)

      try {
        const response = typeof input === 'string'
          ? await api.analyzeText(input, jurisdiction)
          : await api.analyzeFile(input, jurisdiction)

        clearInterval(stageTimer)
        setCurrent(response.data)
        setAnalyzing(false)

        // BUG-24 FIX: navigate to URL that persists across refreshes
        navigate(`/result/${response.data.analysis_id}`)
        toast.success('Analysis complete!')
      } catch (err: unknown) {
        clearInterval(stageTimer)
        setAnalyzing(false)
        const axiosErr = err as { response?: { data?: { detail?: string } } }
        const message = axiosErr?.response?.data?.detail
          ?? 'Analysis failed. Please try again.'
        setError(message)
        toast.error(message)
      }
    },
    [navigate, setAnalyzing, setCurrent, setError]
  )

  return { runAnalysis }
}
