/**
 * Root application router.
 * BUG-24 FIX: /result → /result/:analysisId (URL-persistent results).
 * BUG-25 FIX: Result wrapped in ErrorBoundary.
 * BUG-28 FIX: refreshUser() called on mount to sync plan upgrades from server.
 * BUG-36 FIX: /forgot-password, /reset-password, /verify-email routes added.
 */
import { useEffect, lazy, Suspense } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import Navbar from './components/layout/Navbar'
import { ErrorBoundary } from './components/ErrorBoundary'
import { useAuthStore } from './store/authStore'

// Eager-load pages used on first render
import Home     from './pages/Home'
import Login    from './pages/Login'
import Register from './pages/Register'

// Lazy-load authenticated pages — smaller initial bundle
const Analyze       = lazy(() => import('./pages/Analyze'))
const Result        = lazy(() => import('./pages/Result'))
const History       = lazy(() => import('./pages/History'))
const Pricing       = lazy(() => import('./pages/Pricing'))
const ForgotPassword = lazy(() => import('./pages/ForgotPassword'))
const ResetPassword  = lazy(() => import('./pages/ResetPassword'))
const VerifyEmail    = lazy(() => import('./pages/VerifyEmail'))

function LoadingSpinner() {
  return (
    <div className="min-h-[60vh] flex items-center justify-center">
      <div className="w-8 h-8 border-2 border-navy-500 border-t-transparent
                      rounded-full animate-spin" />
    </div>
  )
}

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user } = useAuthStore()
  if (!user) return <Navigate to="/register" replace />
  return <>{children}</>
}

export default function App() {
  const { user, refreshUser } = useAuthStore()

  // BUG-28 FIX: Sync user data from server on every app load.
  // Catches plan upgrades (e.g. after Stripe checkout) that happened server-side
  // and aren't reflected in the locally-persisted Zustand state yet.
  useEffect(() => {
    if (user) {
      refreshUser()
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="min-h-screen bg-slate-50 font-body">
      <Navbar />
      <main>
        <Suspense fallback={<LoadingSpinner />}>
          <Routes>
            {/* Public */}
            <Route path="/"                element={<Home />} />
            <Route path="/login"           element={<Login />} />
            <Route path="/register"        element={<Register />} />
            <Route path="/pricing"         element={<Pricing />} />
            {/* BUG-36 FIX: auth flow pages */}
            <Route path="/forgot-password" element={<ForgotPassword />} />
            <Route path="/reset-password"  element={<ResetPassword />} />
            <Route path="/verify-email"    element={<VerifyEmail />} />

            {/* Protected */}
            <Route path="/analyze" element={
              <ProtectedRoute><Analyze /></ProtectedRoute>
            } />

            {/* BUG-24 FIX: /:analysisId makes result URL-persistent */}
            {/* BUG-25 FIX: ErrorBoundary catches render crashes */}
            <Route path="/result/:analysisId" element={
              <ProtectedRoute>
                <ErrorBoundary fallbackPath="/analyze">
                  <Result />
                </ErrorBoundary>
              </ProtectedRoute>
            } />

            <Route path="/history" element={
              <ProtectedRoute><History /></ProtectedRoute>
            } />

            {/* 404 */}
            <Route path="*" element={
              <div className="min-h-[60vh] flex flex-col items-center
                              justify-center gap-4 text-center px-4">
                <div className="font-display text-8xl font-bold text-slate-100">
                  404
                </div>
                <h2 className="font-display text-2xl font-bold text-slate-700">
                  Page not found
                </h2>
                <p className="text-sm text-slate-500">
                  The page you're looking for doesn't exist.
                </p>
                <a href="/" className="btn-primary">Go Home</a>
              </div>
            } />
          </Routes>
        </Suspense>
      </main>
    </div>
  )
}
