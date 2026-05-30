import clsx from 'clsx'

type RiskLevel = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'SAFE'
type LegalStatus = 'ILLEGAL' | 'SUSPECT' | 'MISSING' | 'UNFAIR' | 'STANDARD' | 'FAVORABLE_TO_TENANT'

const RISK_STYLES: Record<RiskLevel, string> = {
  CRITICAL: 'bg-red-50 text-red-700 border-red-200 ring-red-100',
  HIGH:     'bg-orange-50 text-orange-700 border-orange-200 ring-orange-100',
  MEDIUM:   'bg-amber-50 text-amber-700 border-amber-200 ring-amber-100',
  LOW:      'bg-green-50 text-green-700 border-green-200 ring-green-100',
  SAFE:     'bg-blue-50 text-blue-700 border-blue-200 ring-blue-100',
}

const STATUS_STYLES: Record<LegalStatus, string> = {
  ILLEGAL:              'bg-red-100 text-red-800 border-red-300',
  SUSPECT:              'bg-orange-100 text-orange-800 border-orange-300',
  MISSING:              'bg-violet-100 text-violet-800 border-violet-300',
  UNFAIR:               'bg-amber-100 text-amber-800 border-amber-300',
  STANDARD:             'bg-slate-100 text-slate-600 border-slate-200',
  FAVORABLE_TO_TENANT:  'bg-green-100 text-green-800 border-green-300',
}

export function RiskBadge({ level }: { level: RiskLevel }) {
  return (
    <span className={clsx(
      'inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-widest border',
      RISK_STYLES[level] || RISK_STYLES.SAFE
    )}>
      {level === 'CRITICAL' && '⚠ '}
      {level}
    </span>
  )
}

export function StatusBadge({ status }: { status: LegalStatus }) {
  const labels: Record<LegalStatus, string> = {
    ILLEGAL: '⛔ Illegal',
    SUSPECT: '🔶 Suspect',
    MISSING: '🟣 Missing',
    UNFAIR: '🟡 Unfair',
    STANDARD: '✓ Standard',
    FAVORABLE_TO_TENANT: '✅ Favorable',
  }
  return (
    <span className={clsx(
      'inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-semibold border',
      STATUS_STYLES[status] || STATUS_STYLES.STANDARD
    )}>
      {labels[status] || status}
    </span>
  )
}
