import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useAuthStore } from '../store/authStore'
import { api } from '../api/client'
import toast from 'react-hot-toast'

const PLANS = [
  {
    id: 'FREE', name: 'Free', price: '₹0', period: 'forever', analyses: '1 per month',
    highlight: false, cta: 'Get Started Free',
    features: [
      '1 lease analysis per month',
      'All 9 Indian jurisdictions',
      'Full clause breakdown',
      'Fairness score 0–100',
      'Counter-proposal letter',
    ],
  },
  {
    id: 'PRO', name: 'Pro', price: '₹299', period: '/month', analyses: 'Unlimited',
    highlight: true, cta: 'Start Pro',
    features: [
      'Unlimited analyses',
      'All Indian jurisdictions',
      'PDF letter download',
      'Email letter directly',
      '90-day analysis history',
      'Priority support',
    ],
  },
  {
    id: 'TEAM', name: 'Team', price: '₹1,499', period: '/month', analyses: 'Unlimited + API',
    highlight: false, cta: 'Start Team',
    features: [
      'Everything in Pro',
      'White-label letters',
      'REST API access',
      'Global jurisdictions',
      'Bulk analysis',
      'Dedicated support',
      'NGO/legal aid discounts',
    ],
  },
]

export default function Pricing() {
  const { user } = useAuthStore()
  const navigate = useNavigate()

  const handleClick = async (planId: string) => {
    if (!user) { navigate('/register'); return }
    if (planId === 'FREE') { navigate('/analyze'); return }
    if (user.plan === planId) { navigate('/analyze'); return }
    try {
      const { data } = await api.createCheckout(planId)
      window.location.href = data.checkout_url
    } catch {
      toast.error('Could not start checkout. Please try again.')
    }
  }

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-16">
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}
        className="text-center mb-12">
        <h1 className="font-display text-4xl font-bold text-slate-900 mb-3">
          Simple, honest pricing
        </h1>
        <p className="text-slate-500 text-sm max-w-md mx-auto">
          One free analysis to try. Upgrade when you need more. Cancel any time.
        </p>
      </motion.div>

      <div className="grid sm:grid-cols-3 gap-5 items-start">
        {PLANS.map((plan, i) => (
          <motion.div key={plan.id}
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className={`relative bg-white border rounded-2xl p-6 ${
              plan.highlight
                ? 'border-navy-500 shadow-xl shadow-navy-500/10 scale-[1.02]'
                : 'border-slate-200 shadow-sm'
            }`}
          >
            {plan.highlight && (
              <div className="absolute -top-3.5 left-1/2 -translate-x-1/2">
                <span className="bg-navy-500 text-white text-[10px] font-bold px-3 py-1
                                 rounded-full uppercase tracking-widest whitespace-nowrap">
                  Most Popular
                </span>
              </div>
            )}
            <div className="mb-5">
              <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-2">
                {plan.name}
              </h3>
              <div className="flex items-baseline gap-1">
                <span className="font-display text-4xl font-bold text-slate-900">
                  {plan.price}
                </span>
                <span className="text-slate-400 text-sm">{plan.period}</span>
              </div>
              <div className="text-xs text-slate-400 mt-1">{plan.analyses} analyses</div>
            </div>
            <ul className="space-y-2.5 mb-6">
              {plan.features.map((f) => (
                <li key={f} className="flex items-start gap-2 text-sm text-slate-600">
                  <span className="text-green-500 flex-shrink-0 font-bold mt-px">✓</span>
                  {f}
                </li>
              ))}
            </ul>
            <button
              onClick={() => handleClick(plan.id)}
              className={`w-full py-3 rounded-xl font-semibold text-sm transition-all
                          active:scale-[0.98] ${
                user?.plan === plan.id
                  ? 'bg-slate-100 text-slate-500 cursor-default'
                  : plan.highlight
                  ? 'bg-navy-500 text-white hover:bg-navy-600 shadow-lg shadow-navy-500/20'
                  : 'border border-slate-200 text-slate-700 hover:bg-slate-50'
              }`}
            >
              {user?.plan === plan.id ? '✓ Current Plan' : plan.cta}
            </button>
          </motion.div>
        ))}
      </div>

      <div className="mt-12 text-center text-xs text-slate-400 space-y-1">
        <p>All prices in INR + applicable GST · Payments secured by Stripe · Cancel any time</p>
        <p>
          NGOs and legal aid organizations:{' '}
          <a href="mailto:hello@leaselens.in" className="underline hover:text-slate-600">
            contact us
          </a>{' '}
          for discounted access
        </p>
      </div>
    </div>
  )
}
