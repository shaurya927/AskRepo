import React, { useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { AlertCircle } from 'lucide-react'
import { useAnalysisStatus } from '../hooks/useAnalysisStatus'
import ProgressSteps from '../components/ProgressSteps'

import Aurora from '../components/Aurora'
import ShinyText from '../components/ShinyText'
import ThemeToggle from '../components/ThemeToggle'
import { GitBranch } from 'lucide-react'
import { useTheme } from '../hooks/useTheme'

const AnalysisProgressPage: React.FC = () => {
  const { jobId } = useParams<{ jobId: string }>()
  const navigate = useNavigate()
  const { theme } = useTheme()
  
  const { status, progressDetail, repositoryId, isComplete, isFailed, error } = useAnalysisStatus(jobId)

  useEffect(() => {
    if (isComplete && repositoryId) {
      const timer = setTimeout(() => {
        navigate(`/repo/${repositoryId}`)
      }, 1000)
      return () => clearTimeout(timer)
    }
  }, [isComplete, repositoryId, navigate])

  return (
    <div className="flex-1 flex flex-col h-full overflow-y-auto relative bg-white dark:bg-[#000000]">
      <div className="fixed inset-0 z-0 pointer-events-none opacity-60 dark:opacity-30">
        <Aurora 
          colorStops={theme === 'dark' ? ['#1a365d', '#000000', '#58a6ff'] : ['#f0f9ff', '#ffffff', '#e0f2fe']} 
          blend={0.6} 
          speed={0.5} 
        />
      </div>
      <div className="absolute top-6 right-6 z-50 flex items-center gap-3">
        <a
          href="https://github.com/shaurya927/AskRepo"
          target="_blank"
          rel="noopener noreferrer"
          className="text-gray-500 hover:text-gray-900 dark:text-[#8b949e] dark:hover:text-[#e6edf3] transition-colors"
        >
          <GitBranch size={20} />
        </a>
        <ThemeToggle />
      </div>
      <div className="flex-1 flex flex-col items-center justify-center p-6 relative z-10 w-full">
      <div className="w-full max-w-2xl bg-transparent border-none rounded-xl p-8 text-center">
        <h2 className="text-3xl font-semibold mb-12">
          <ShinyText 
            text="Analyzing Repository" 
            speed={2.5} 
            className="inline-block" 
            color={theme === 'dark' ? '#b5b5b5' : '#475569'}
            shineColor={theme === 'dark' ? '#ffffff' : '#0f172a'}
          />
        </h2>
        
        {isFailed ? (
          <div className="flex flex-col items-center">
            <div className="w-16 h-16 rounded-full bg-[#ffebe9] dark:bg-red-900/20 flex items-center justify-center text-[#f85149] mb-4">
              <AlertCircle size={32} />
            </div>
            <h3 className="text-xl font-medium text-gray-900 dark:text-[#e6edf3] mb-2">Analysis Failed</h3>
            <p className="text-gray-500 dark:text-[#8b949e] mb-6 max-w-md">
              {error || progressDetail || 'An unexpected error occurred during analysis.'}
            </p>
            <button
              onClick={() => navigate('/')}
              className="px-6 py-2 bg-gray-100 dark:bg-[#18181b] hover:bg-gray-200 dark:hover:bg-[#27272a] text-gray-900 dark:text-[#e6edf3] rounded-md font-medium transition-colors border border-gray-300 dark:border-[#27272a]"
            >
              Try Again
            </button>
          </div>
        ) : (
          <div className="text-left max-w-sm mx-auto scale-110 transform">
            <ProgressSteps currentStatus={status} progressDetail={progressDetail} />
          </div>
        )}
      </div>
    </div>
    </div>
  )
}

export default AnalysisProgressPage
