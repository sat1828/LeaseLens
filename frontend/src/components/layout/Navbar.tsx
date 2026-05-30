/**
 * Navigation bar.
 * BUG-34 FIX: Full mobile hamburger menu with animated drawer.
 *             Without this, all nav links were hidden below 768px.
 */
import { useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuthStore } from '../../store/authStore'

export default function Navbar() {
  const { user, logout } = useAuthStore()
  const navigate         = useNavigate()
  const location         = useLocation()
  const [mobileOpen, setMobileOpen] = useState(false)

  const handleLogout = () => {
    logout()
    setMobileOpen(false)
    navigate('/')
  }

  const planBadge: Record<string, string> = {
    FREE: 'bg-slate-100 text-slate-600',
    PRO:  'bg-blue-100 text-blue-700',
    TEAM: 'bg-violet-100 text-violet-700',
  }

  const isActive = (path: string) =>
    location.pathname === path
      ? 'text-navy-700 font-semibold'
      : 'text-slate-500 hover:text-slate-800'

  const navLinks = (
    <>
      <Link to="/pricing" onClick={() => setMobileOpen(false)}
        className={`transition-colors ${isActive('/pricing')}`}>
        Pricing
      </Link>
      {user && (
        <Link to="/analyze" onClick={() => setMobileOpen(false)}
          className={`transition-colors ${isActive('/analyze')}`}>
          Analyze
        </Link>
      )}
      {user && (
        <Link to="/history" onClick={() => setMobileOpen(false)}
          className={`transition-colors ${isActive('/history')}`}>
          My Analyses
        </Link>
      )}
    </>
  )

  return (
    <>
      <nav className="sticky top-0 z-50 bg-white/90 backdrop-blur-md border-b border-slate-100">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center
                        justify-between gap-4">

          {/* Logo */}
          <Link to="/" className="flex items-center gap-2.5 flex-shrink-0 group">
            <div className="w-8 h-8 rounded-lg bg-navy-500 flex items-center justify-center
                            text-white text-sm font-bold shadow-sm
                            group-hover:bg-navy-600 transition-colors">
              ⚖
            </div>
            <span className="font-display text-lg font-bold text-navy-700
                             group-hover:text-navy-500 transition-colors">
              LeaseLens
            </span>
          </Link>

          {/* Desktop nav links */}
          <div className="hidden md:flex items-center gap-6 text-sm">
            {navLinks}
          </div>

          {/* Right: auth + hamburger */}
          <div className="flex items-center gap-3 flex-shrink-0">
            {user ? (
              <>
                <span className={`hidden sm:inline text-[11px] font-bold px-2.5 py-1
                                   rounded-full ${planBadge[user.plan] ?? planBadge.FREE}`}>
                  {user.plan}
                </span>
                <span className="hidden md:inline text-sm text-slate-400 max-w-[120px] truncate">
                  {user.full_name ?? user.email.split('@')[0]}
                </span>
                <button
                  onClick={handleLogout}
                  className="hidden md:inline text-sm text-slate-400
                             hover:text-slate-700 transition-colors"
                >
                  Logout
                </button>
              </>
            ) : (
              <>
                <Link to="/login"
                  className="hidden md:inline text-sm font-medium text-slate-600
                             hover:text-slate-900 transition-colors">
                  Login
                </Link>
                <Link to="/register"
                  className="hidden md:inline text-sm font-semibold px-4 py-2
                             bg-navy-500 text-white rounded-xl hover:bg-navy-600
                             transition-colors shadow-sm">
                  Get Started Free
                </Link>
              </>
            )}

            {/* BUG-34 FIX: Hamburger — visible only on mobile */}
            <button
              className="md:hidden p-2 -mr-1 text-slate-500 hover:text-slate-800
                         transition-colors rounded-lg hover:bg-slate-100"
              onClick={() => setMobileOpen(!mobileOpen)}
              aria-label={mobileOpen ? 'Close menu' : 'Open menu'}
              aria-expanded={mobileOpen}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                {mobileOpen ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M4 6h16M4 12h16M4 18h16" />
                )}
              </svg>
            </button>
          </div>
        </div>
      </nav>

      {/* BUG-34 FIX: Mobile drawer — animated, accessible */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2, ease: 'easeInOut' }}
            className="md:hidden bg-white border-b border-slate-100 sticky top-16 z-40
                       overflow-hidden shadow-sm"
          >
            <div className="px-4 py-3 space-y-0.5">
              <Link to="/pricing" onClick={() => setMobileOpen(false)}
                className="block py-2.5 px-2 text-sm font-medium text-slate-700
                           hover:text-navy-600 hover:bg-slate-50 rounded-lg transition-colors">
                Pricing
              </Link>
              {user && (
                <Link to="/analyze" onClick={() => setMobileOpen(false)}
                  className="block py-2.5 px-2 text-sm font-medium text-slate-700
                             hover:text-navy-600 hover:bg-slate-50 rounded-lg transition-colors">
                  Analyze a Lease
                </Link>
              )}
              {user && (
                <Link to="/history" onClick={() => setMobileOpen(false)}
                  className="block py-2.5 px-2 text-sm font-medium text-slate-700
                             hover:text-navy-600 hover:bg-slate-50 rounded-lg transition-colors">
                  My Analyses
                </Link>
              )}
              {user ? (
                <>
                  <div className="px-2 py-2 text-xs text-slate-400 flex items-center gap-2">
                    <span className={`text-[11px] font-bold px-2 py-0.5 rounded-full
                                      ${planBadge[user.plan] ?? planBadge.FREE}`}>
                      {user.plan}
                    </span>
                    <span className="truncate">
                      {user.full_name ?? user.email}
                    </span>
                  </div>
                  <button onClick={handleLogout}
                    className="block w-full text-left py-2.5 px-2 text-sm font-medium
                               text-red-500 hover:bg-red-50 rounded-lg transition-colors">
                    Logout
                  </button>
                </>
              ) : (
                <>
                  <Link to="/login" onClick={() => setMobileOpen(false)}
                    className="block py-2.5 px-2 text-sm font-medium text-slate-700
                               hover:bg-slate-50 rounded-lg transition-colors">
                    Login
                  </Link>
                  <Link to="/register" onClick={() => setMobileOpen(false)}
                    className="block py-2.5 px-2 text-sm font-semibold text-navy-600
                               hover:bg-navy-50 rounded-lg transition-colors">
                    Get Started Free →
                  </Link>
                </>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  )
}
