import React, { useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { AlertCircle } from 'lucide-react'
import { useAnalysisStatus } from '../hooks/useAnalysisStatus'
import ProgressSteps from '../components/ProgressSteps'

const AnalysisProgressPage: React.FC = () => {
  const { jobId } = useParams<{ jobId: string }>()
  const navigate = useNavigate()
  
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
    <div className="flex-1 flex flex-col items-center justify-center p-6">
      <div className="w-full max-w-2xl bg-white dark:bg-[#161b22] border border-gray-200 dark:border-[#30363d] rounded-xl shadow-sm p-8 text-center">
        <h2 className="text-2xl font-semibold text-gray-900 dark:text-[#e6edf3] mb-8">
          Analyzing Repository
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
              className="px-6 py-2 bg-gray-100 dark:bg-[#21262d] hover:bg-gray-200 dark:hover:bg-[#30363d] text-gray-900 dark:text-[#e6edf3] rounded-md font-medium transition-colors border border-gray-300 dark:border-[#30363d]"
            >
              Try Again
            </button>
          </div>
        ) : (
          <div className="text-left max-w-sm mx-auto">
            <ProgressSteps currentStatus={status} progressDetail={progressDetail} />
          </div>
        )}
      </div>
    </div>
  )
}

export default AnalysisProgressPage
