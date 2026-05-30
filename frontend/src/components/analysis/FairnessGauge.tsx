import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'

interface Props {
  score: number
  size?: number
}

const BANDS = [
  { min: 80, label: 'Tenant-Favorable', color: '#16A34A', track: '#DCFCE7' },
  { min: 60, label: 'Acceptable', color: '#65A30D', track: '#ECFCCB' },
  { min: 40, label: 'Risky', color: '#D97706', track: '#FEF3C7' },
  { min: 20, label: 'Predatory', color: '#DC2626', track: '#FEE2E2' },
  { min: 0,  label: 'Illegal Agreement', color: '#991B1B', track: '#FEE2E2' },
]

function getBand(score: number) {
  return BANDS.find((b) => score >= b.min) || BANDS[BANDS.length - 1]
}

export default function FairnessGauge({ score, size = 160 }: Props) {
  const [displayed, setDisplayed] = useState(0)
  const band = getBand(score)
  const r = (size / 2) * 0.72
  const cx = size / 2
  const cy = size / 2
  const circ = 2 * Math.PI * r
  const offset = circ - (displayed / 100) * circ

  useEffect(() => {
    let start: number | null = null
    const duration = 1600
    const step = (ts: number) => {
      if (!start) start = ts
      const p = Math.min((ts - start) / duration, 1)
      const ease = 1 - Math.pow(1 - p, 4) // easeOutQuart
      setDisplayed(Math.round(ease * score))
      if (p < 1) requestAnimationFrame(step)
    }
    const id = requestAnimationFrame(step)
    return () => cancelAnimationFrame(id)
  }, [score])

  return (
    <div className="flex flex-col items-center gap-3">
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        {/* Background track */}
        <circle
          cx={cx} cy={cy} r={r}
          fill="none"
          stroke={band.track}
          strokeWidth={size * 0.1}
        />
        {/* Progress arc */}
        <motion.circle
          cx={cx} cy={cy} r={r}
          fill="none"
          stroke={band.color}
          strokeWidth={size * 0.1}
          strokeLinecap="round"
          strokeDasharray={circ}
          strokeDashoffset={offset}
          transform={`rotate(-90 ${cx} ${cy})`}
          style={{ transition: 'stroke-dashoffset 0.04s linear' }}
        />
        {/* Score number */}
        <text
          x={cx} y={cy - size * 0.04}
          textAnchor="middle"
          fontSize={size * 0.2}
          fontWeight="800"
          fill={band.color}
          fontFamily="Playfair Display, Georgia, serif"
        >
          {displayed}
        </text>
        <text
          x={cx} y={cy + size * 0.12}
          textAnchor="middle"
          fontSize={size * 0.07}
          fill="#94A3B8"
          fontFamily="DM Sans, system-ui"
        >
          / 100
        </text>
      </svg>

      <div className="text-center">
        <div
          className="text-sm font-bold uppercase tracking-widest"
          style={{ color: band.color }}
        >
          {band.label}
        </div>
        <div className="text-xs text-slate-400 mt-0.5">Fairness Score</div>
      </div>
    </div>
  )
}
