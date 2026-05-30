import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { motion, AnimatePresence } from 'framer-motion'
import clsx from 'clsx'

const JURISDICTIONS = [
  'Bengaluru, Karnataka, India',
  'Mumbai, Maharashtra, India',
  'Delhi NCR, India',
  'Hyderabad, Telangana, India',
  'Chennai, Tamil Nadu, India',
  'Pune, Maharashtra, India',
  'Kolkata, West Bengal, India',
  'Ahmedabad, Gujarat, India',
  'Bhubaneswar, Odisha, India',
  'Jaipur, Rajasthan, India',
  'Lucknow, Uttar Pradesh, India',
  'Kochi, Kerala, India',
]

const DEMO_LEASE = `RENTAL AGREEMENT — BENGALURU

Between: Rajesh Kumar (Landlord) and Ananya Singh (Tenant)
Property: Flat 12B, Prestige Towers, Whitefield, Bengaluru 560066
Monthly Rent: Rs. 28,000
Security Deposit: Rs. 1,12,000 (Four months)
Duration: 11 months from 1st March 2024

1. SECURITY DEPOSIT: Tenant shall pay Rs 1,12,000 as refundable deposit. Landlord may deduct any amounts at sole discretion. Refund within 6 months of vacating.

2. ENTRY: Landlord or agents may enter the premises at any time without prior notice for inspection or repairs.

3. UTILITIES: If rent remains unpaid for more than 10 days, Landlord reserves right to disconnect electricity and water supply.

4. EVICTION: Landlord may terminate this agreement and demand vacant possession with 7 days written notice for any reason.

5. RENT ESCALATION: Rent shall increase by 20% annually. No prior notice required.

6. MAINTENANCE: Tenant is solely responsible for all repairs and maintenance including structural, plumbing, electrical work. Landlord has zero maintenance obligation.

7. DISPUTES: All disputes shall be resolved through private arbitration only. Tenant expressly waives all rights to approach Rent Tribunal, Civil Court, or any Government Authority.

8. PENALTY: Late payment attracts Rs. 1,000 per day. Landlord may retain entire security deposit for any breach.

9. LOCK-IN: 9-month lock-in period. Early exit requires payment of 4 months rent as penalty.

10. SUBLETTING: No subletting permitted. Violation results in immediate eviction and forfeiture of deposit.`

interface Props {
  jurisdiction: string
  onJurisdictionChange: (v: string) => void
  onSubmit: (input: File | string) => void
  disabled?: boolean
}

export default function UploadPanel({ jurisdiction, onJurisdictionChange, onSubmit, disabled }: Props) {
  const [mode, setMode] = useState<'file' | 'text'>('file')
  const [file, setFile] = useState<File | null>(null)
  const [text, setText] = useState('')

  const onDrop = useCallback((accepted: File[]) => {
    if (accepted[0]) setFile(accepted[0])
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    maxFiles: 1,
    maxSize: 25 * 1024 * 1024,
    disabled,
  })

  const canSubmit = mode === 'file' ? !!file : text.trim().length > 100

  const handleSubmit = () => {
    if (disabled) return
    if (mode === 'file' && file) onSubmit(file)
    else if (mode === 'text' && text.trim().length > 100) onSubmit(text.trim())
  }

  return (
    <div className="space-y-5">
      {/* Mode toggle */}
      <div className="flex rounded-xl overflow-hidden border border-slate-200 bg-slate-50 p-1">
        {(['file', 'text'] as const).map((m) => (
          <button
            key={m}
            onClick={() => setMode(m)}
            className={clsx(
              'flex-1 py-2 text-sm font-medium rounded-lg transition-all',
              mode === m ? 'bg-white text-navy-700 shadow-sm' : 'text-slate-500 hover:text-slate-700'
            )}
          >
            {m === 'file' ? '📄 Upload PDF' : '✏️ Paste Text'}
          </button>
        ))}
      </div>

      <AnimatePresence mode="wait">
        {mode === 'file' ? (
          <motion.div
            key="file"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.2 }}
          >
            <div
              {...getRootProps()}
              className={clsx(
                'border-2 border-dashed rounded-2xl p-10 text-center cursor-pointer transition-all duration-200',
                isDragActive ? 'border-navy-500 bg-navy-50' :
                file ? 'border-green-400 bg-green-50' :
                'border-slate-200 bg-slate-50 hover:border-slate-300 hover:bg-white'
              )}
            >
              <input {...getInputProps()} />
              {file ? (
                <div>
                  <div className="text-3xl mb-2">✅</div>
                  <p className="font-semibold text-green-700 text-sm">{file.name}</p>
                  <p className="text-xs text-slate-400 mt-1">{(file.size / 1024).toFixed(0)} KB · Click to replace</p>
                </div>
              ) : isDragActive ? (
                <div>
                  <div className="text-3xl mb-2">📂</div>
                  <p className="font-semibold text-navy-600 text-sm">Drop it here</p>
                </div>
              ) : (
                <div>
                  <div className="text-4xl mb-3">📄</div>
                  <p className="font-semibold text-slate-700 text-sm">Drag & drop your lease PDF</p>
                  <p className="text-xs text-slate-400 mt-1">or click to browse · Max 25 MB · PDF only</p>
                </div>
              )}
            </div>
          </motion.div>
        ) : (
          <motion.div
            key="text"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.2 }}
          >
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Paste the full text of your rental agreement here…"
              className="w-full h-44 px-4 py-3 text-sm text-slate-700 border border-slate-200 rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-navy-500/30 focus:border-navy-400 transition-all font-mono placeholder:font-sans"
            />
            <div className="flex justify-between items-center mt-1.5">
              <span className="text-xs text-slate-400">
                {text.length} chars {text.length > 0 && text.length < 100 && '· need 100+'}
              </span>
              <button
                onClick={() => { setMode('text'); setText(DEMO_LEASE) }}
                className="text-xs text-navy-500 hover:text-navy-700 font-medium transition-colors"
              >
                Load demo lease →
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Jurisdiction */}
      <div>
        <label className="block text-xs font-semibold text-slate-500 uppercase tracking-widest mb-2">
          Your City / Jurisdiction
        </label>
        <select
          value={jurisdiction}
          onChange={(e) => onJurisdictionChange(e.target.value)}
          className="w-full px-4 py-3 text-sm text-slate-700 border border-slate-200 rounded-xl bg-white focus:outline-none focus:ring-2 focus:ring-navy-500/30 focus:border-navy-400 transition-all"
        >
          {JURISDICTIONS.map((j) => (
            <option key={j} value={j}>{j}</option>
          ))}
        </select>
      </div>

      {/* Submit */}
      <button
        onClick={handleSubmit}
        disabled={!canSubmit || disabled}
        className={clsx(
          'w-full py-4 rounded-xl font-semibold text-sm tracking-wide transition-all duration-200',
          canSubmit && !disabled
            ? 'bg-navy-500 text-white hover:bg-navy-600 active:scale-[0.98] shadow-lg shadow-navy-500/20'
            : 'bg-slate-100 text-slate-400 cursor-not-allowed'
        )}
      >
        🔍 Analyze My Lease
      </button>

      <p className="text-center text-xs text-slate-400">
        Your lease is never stored · Processed in memory only · Not legal advice
      </p>
    </div>
  )
}
