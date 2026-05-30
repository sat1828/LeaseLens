/**
 * BUG-25 FIX: React Error Boundary
 * Catches render errors so users never see a blank white screen.
 * Shows a friendly recovery UI instead.
 */
import { Component, ReactNode } from 'react'

interface Props {
  children: ReactNode
  fallbackPath?: string
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: { componentStack: string }) {
    // In production, send to error tracking (e.g. Sentry)
    console.error('[LeaseLens] Render error:', error.message, info.componentStack)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-[60vh] flex flex-col items-center justify-center gap-4 text-center px-4">
          <div className="text-5xl">⚠️</div>
          <h2 className="font-display text-xl font-bold text-slate-900">
            Something went wrong
          </h2>
          <p className="text-sm text-slate-500 max-w-sm">
            We couldn't display this page. This is likely a temporary issue.
          </p>
          <div className="flex gap-3">
            <button
              onClick={() => this.setState({ hasError: false, error: null })}
              className="btn-secondary"
            >
              Try again
            </button>
            <button
              onClick={() => {
                this.setState({ hasError: false, error: null })
                window.location.href = this.props.fallbackPath || '/analyze'
              }}
              className="btn-primary"
            >
              New Analysis
            </button>
          </div>
          {/* Show stack trace in development only */}
          {import.meta.env.DEV && this.state.error && (
            <pre className="text-left text-xs text-red-600 bg-red-50 p-4 rounded-lg
                            max-w-2xl overflow-auto mt-4 w-full">
              {this.state.error.stack}
            </pre>
          )}
        </div>
      )
    }
    return this.props.children
  }
}
