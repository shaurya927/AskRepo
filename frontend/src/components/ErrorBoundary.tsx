import { Component } from 'react'
import type { ErrorInfo, ReactNode } from 'react'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null
  }

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error:', error, errorInfo)
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-[#000000] p-4">
          <div className="max-w-md w-full bg-white dark:bg-[#111111] border border-gray-200 dark:border-[#27272a] rounded-lg p-6 text-center shadow-sm">
            <h2 className="text-xl font-semibold text-[#f85149] mb-4">Something went wrong</h2>
            <p className="text-gray-600 dark:text-[#8b949e] mb-6 text-sm">
              {this.state.error?.message || 'An unexpected error occurred.'}
            </p>
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-[#238636] hover:bg-[#2ea043] text-white rounded-md text-sm font-medium transition-colors"
            >
              Reload page
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary
