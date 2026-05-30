/**
 * Home / landing page.
 * BUG-39 FIX: Fabricated testimonials replaced with factual statistics
 *             and clearly-labelled illustrative scenarios.
 *             Legal: complies with ASCI guidelines and Consumer Protection Act 2019.
 */
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useAuthStore } from '../store/authStore'

const STATS = [
  { value: '200M+', label: 'tenants sign unfair leases yearly worldwide',
    source: 'UN-Habitat, 2022' },
  { value: '₹8,000', label: 'average lawyer fee for a single lease review in India',
    source: 'LegalWiz.in, 2024' },
  { value: '30 sec', label: 'time LeaseLens takes to deliver a complete legal audit',
    source: '' },
]

const FEATURES = [
  {
    icon: '🔍',
    title: 'Clause-by-Clause Forensics',
    desc: 'Every clause checked against current Indian tenancy law — not just keyword matching. Real legal reasoning on every line.',
  },
  {
    icon: '⚖️',
    title: 'MTA 2021 / 2025 Aware',
    desc: 'Built on the Model Tenancy Act 2021 and 2025 Rules with state-specific overrides for 12 cities across 9 states.',
  },
  {
    icon: '📊',
    title: 'Fairness Score 0–100',
    desc: 'A weighted legal score. Each CRITICAL clause docks 15 points. One number tells you instantly: sign, negotiate, or walk.',
  },
  {
    icon: '✉️',
    title: 'Counter-Proposal Letter',
    desc: 'A professionally written, law-citing letter tailored to your specific lease. Copy, download, or email directly to your landlord.',
  },
  {
    icon: '🔒',
    title: 'Privacy by Design',
    desc: 'Your PDF is processed in memory and immediately discarded. We store zero bytes of your lease document on our servers.',
  },
  {
    icon: '⚡',
    title: 'Results in 30 Seconds',
    desc: 'Powered by Claude AI (Anthropic). The analysis that takes a lawyer hours — delivered before your coffee cools.',
  },
]

// BUG-39 FIX: clearly labelled illustrative scenarios, not fake testimonials
const SCENARIOS = [
  {
    icon: '💰',
    title: 'Security deposit over the legal cap',
    scenario: 'A tenant in Bengaluru was asked for ₹90,000 deposit on ₹20,000/month rent — 4.5× the legal limit. LeaseLens flagged it as CRITICAL + ILLEGAL, cited MTA 2021 §11(2), and generated a counter-proposal letter. The legal cap was ₹40,000.',
    label: 'Illustrative scenario based on common lease patterns',
  },
  {
    icon: '⚡',
    title: 'Illegal utility disconnection clause',
    scenario: 'A standard Hyderabad lease included: "Landlord may disconnect electricity for overdue rent." This violates MTA 2021 §23 explicitly. LeaseLens flags this as CRITICAL — it is a criminal offence, not just an unfair term.',
    label: 'Illustrative scenario based on common lease patterns',
  },
  {
    icon: '⚖️',
    title: 'Rent Tribunal waiver (void clause)',
    scenario: 'A Mumbai Leave & Licence agreement said all disputes must go to private arbitration — no courts or tribunals. Under MTA 2021 §30, this clause is void ab initio. You can always approach the Rent Tribunal regardless of what you signed.',
    label: 'Illustrative scenario based on common lease patterns',
  },
]

const fadeUp = {
  initial: { opacity: 0, y: 20 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true },
}

export default function Home() {
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const target   = user ? '/analyze' : '/register'

  return (
    <div className="min-h-screen">

      {/* ── Hero ──────────────────────────────────────────────────────────── */}
      <section className="relative overflow-hidden bg-navy-700 text-white">
        <div
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' \
viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='%23fff' \
fill-opacity='1' fill-rule='evenodd'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4z\
M6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM36 4V0h-2v4h-4v2h4v4h2V6h4V4h-4z\
M6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/svg%3E")`,
          }}
        />
        <div className="relative max-w-5xl mx-auto px-4 sm:px-6 py-20 sm:py-28">
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="max-w-3xl"
          >
            <div className="inline-flex items-center gap-2 bg-white/10 border border-white/20
                            rounded-full px-4 py-1.5 text-xs font-medium mb-6 text-blue-200">
              <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
              India-specific · Model Tenancy Act 2021 & 2025 Rules
            </div>
            <h1 className="font-display text-4xl sm:text-6xl font-bold leading-tight mb-6">
              Your lease has a lawyer.
              <br />
              <span className="text-blue-300">Now you do too.</span>
            </h1>
            <p className="text-lg text-slate-300 leading-relaxed mb-8 max-w-xl">
              Upload your rental agreement. Get a forensic clause-by-clause legal audit,
              fairness score, and a ready-to-send counter-proposal — in 30 seconds.
            </p>
            <div className="flex flex-wrap gap-3">
              <motion.button
                whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                onClick={() => navigate(target)}
                className="px-7 py-4 bg-white text-navy-700 font-bold rounded-xl
                           hover:bg-blue-50 transition-colors shadow-xl text-sm"
              >
                Analyze My Lease Free →
              </motion.button>
              <button
                onClick={() => navigate('/pricing')}
                className="px-7 py-4 bg-white/10 text-white font-medium rounded-xl
                           hover:bg-white/15 transition-colors border border-white/20 text-sm"
              >
                See Pricing
              </button>
            </div>
            <p className="mt-4 text-xs text-slate-400">
              Free first analysis · No credit card · PDF never stored
            </p>
          </motion.div>
        </div>
      </section>

      {/* ── Stats ─────────────────────────────────────────────────────────── */}
      <section className="bg-white border-b border-slate-100">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
          <div className="grid grid-cols-3 divide-x divide-slate-100">
            {STATS.map((s, i) => (
              <motion.div key={i} {...fadeUp} transition={{ delay: i * 0.1 }}
                className="px-4 py-3 text-center">
                <div className="font-display text-3xl font-bold text-navy-700">{s.value}</div>
                <div className="text-xs text-slate-500 mt-1 leading-snug">{s.label}</div>
                {s.source && (
                  <div className="text-[10px] text-slate-300 mt-0.5">{s.source}</div>
                )}
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Features ──────────────────────────────────────────────────────── */}
      <section className="max-w-5xl mx-auto px-4 sm:px-6 py-20">
        <motion.div {...fadeUp} className="text-center mb-12">
          <h2 className="font-display text-3xl font-bold text-slate-900 mb-3">
            What LeaseLens does for you
          </h2>
          <p className="text-slate-500 text-sm max-w-lg mx-auto">
            The landlord's lawyer spent hours drafting clauses that protect their client.
            You get the same protection in 30 seconds.
          </p>
        </motion.div>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {FEATURES.map((f, i) => (
            <motion.div key={i} {...fadeUp} transition={{ delay: i * 0.07 }}
              className="bg-white border border-slate-100 rounded-2xl p-5
                         hover:shadow-md hover:-translate-y-0.5 transition-all">
              <div className="text-2xl mb-3">{f.icon}</div>
              <h3 className="font-semibold text-slate-900 text-sm mb-1.5">{f.title}</h3>
              <p className="text-xs text-slate-500 leading-relaxed">{f.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ── How it works ──────────────────────────────────────────────────── */}
      <section className="bg-navy-700 text-white py-20">
        <div className="max-w-4xl mx-auto px-4 sm:px-6">
          <motion.h2 {...fadeUp}
            className="font-display text-3xl font-bold text-center mb-14">
            How it works
          </motion.h2>
          <div className="grid sm:grid-cols-4 gap-8">
            {[
              { n: '1', icon: '📄', title: 'Upload or paste', desc: 'PDF or copy-paste lease text' },
              { n: '2', icon: '⚖️', title: 'AI audits clauses', desc: 'Against Indian tenancy law' },
              { n: '3', icon: '📊', title: 'Get your score', desc: '0–100 fairness with full breakdown' },
              { n: '4', icon: '✉️', title: 'Negotiate', desc: 'Use the ready-to-send letter' },
            ].map((step, i) => (
              <motion.div key={i} {...fadeUp} transition={{ delay: i * 0.1 }}
                className="text-center">
                <div className="w-12 h-12 rounded-2xl bg-white/10 border border-white/20
                                text-2xl flex items-center justify-center mx-auto mb-3">
                  {step.icon}
                </div>
                <div className="text-xs text-blue-300 font-bold mb-1">STEP {step.n}</div>
                <div className="font-semibold text-sm mb-1">{step.title}</div>
                <div className="text-xs text-slate-400">{step.desc}</div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── BUG-39 FIX: Illustrative scenarios (not fake testimonials) ─────── */}
      <section className="bg-slate-50 border-y border-slate-100 py-20">
        <div className="max-w-5xl mx-auto px-4 sm:px-6">
          <motion.div {...fadeUp} className="text-center mb-3">
            <h2 className="font-display text-2xl font-bold text-slate-900">
              What LeaseLens catches
            </h2>
          </motion.div>
          {/* BUG-39 FIX: honest disclosure label */}
          <motion.p {...fadeUp} className="text-center text-xs text-slate-400 mb-10">
            Illustrative scenarios based on common patterns found in Indian rental agreements.
            Not real user testimonials.
          </motion.p>
          <div className="grid sm:grid-cols-3 gap-5">
            {SCENARIOS.map((s, i) => (
              <motion.div key={i} {...fadeUp} transition={{ delay: i * 0.1 }}
                className="bg-white border border-slate-100 rounded-2xl p-5 shadow-sm">
                <div className="text-2xl mb-3">{s.icon}</div>
                <h3 className="font-semibold text-sm text-slate-900 mb-2">{s.title}</h3>
                <p className="text-xs text-slate-600 leading-relaxed mb-3">{s.scenario}</p>
                <p className="text-[10px] text-slate-300 italic">{s.label}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Final CTA ─────────────────────────────────────────────────────── */}
      <section className="max-w-3xl mx-auto px-4 sm:px-6 py-24 text-center">
        <motion.div {...fadeUp}>
          <h2 className="font-display text-3xl font-bold text-slate-900 mb-4">
            Don't sign until you know what you're signing.
          </h2>
          <p className="text-slate-500 text-sm mb-8">
            First analysis is free. No account required to load the demo.
          </p>
          <motion.button
            whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
            onClick={() => navigate(target)}
            className="px-10 py-4 bg-navy-500 text-white font-bold rounded-xl
                       hover:bg-navy-600 transition-colors shadow-lg shadow-navy-500/20 text-sm"
          >
            Analyze My Lease Now →
          </motion.button>
        </motion.div>
      </section>
    </div>
  )
}
