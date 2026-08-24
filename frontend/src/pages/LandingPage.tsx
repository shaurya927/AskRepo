import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { GitBranch, Scan, MessageSquare } from 'lucide-react'
import RepoInput from '../components/RepoInput'
import ZipUpload from '../components/ZipUpload'
import { createRepositoryFromURL, createRepositoryFromZip } from '../services/api'

const LandingPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'github' | 'zip'>('github')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()

  const handleUrlSubmit = async (url: string) => {
    try {
      setIsLoading(true)
      setError(null)
      const res = await createRepositoryFromURL(url)
      navigate(`/analysis/${res.job_id}`)
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to submit repository')
      setIsLoading(false)
    }
  }

  const handleZipSubmit = async (file: File) => {
    try {
      setIsLoading(true)
      setError(null)
      const res = await createRepositoryFromZip(file)
      navigate(`/analysis/${res.job_id}`)
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to upload ZIP')
      setIsLoading(false)
    }
  }

  return (
    <div className="flex-1 flex flex-col items-center py-16 px-4 sm:px-6 lg:px-8">
      <div className="text-center max-w-3xl mx-auto mb-12">
        <h1 className="text-4xl sm:text-5xl font-bold tracking-tight text-gray-900 dark:text-[#e6edf3] mb-4">
          AskRepo
        </h1>
        <p className="text-xl sm:text-2xl font-medium text-gray-700 dark:text-[#c9d1d9] mb-2">
          Ask your codebase anything.
        </p>
        <p className="text-lg text-gray-500 dark:text-[#8b949e]">
          AI-powered codebase intelligence. Understand any repository in minutes.
        </p>
      </div>

      <div className="w-full max-w-2xl mx-auto bg-white dark:bg-[#161b22] border border-gray-200 dark:border-[#30363d] rounded-xl shadow-sm p-6 mb-16">
        <div className="flex p-1 bg-gray-100 dark:bg-[#0d1117] rounded-lg mb-6 max-w-sm mx-auto">
          <button
            onClick={() => setActiveTab('github')}
            className={`flex-1 py-2 text-sm font-medium rounded-md transition-all ${
              activeTab === 'github'
                ? 'bg-white dark:bg-[#21262d] text-gray-900 dark:text-[#e6edf3] shadow-sm'
                : 'text-gray-500 dark:text-[#8b949e] hover:text-gray-700 dark:hover:text-[#c9d1d9]'
            }`}
          >
            GitHub URL
          </button>
          <button
            onClick={() => setActiveTab('zip')}
            className={`flex-1 py-2 text-sm font-medium rounded-md transition-all ${
              activeTab === 'zip'
                ? 'bg-white dark:bg-[#21262d] text-gray-900 dark:text-[#e6edf3] shadow-sm'
                : 'text-gray-500 dark:text-[#8b949e] hover:text-gray-700 dark:hover:text-[#c9d1d9]'
            }`}
          >
            Upload ZIP
          </button>
        </div>

        {error && (
          <div className="mb-6 p-3 bg-[#ffebe9] dark:bg-red-900/20 border border-[#f85149]/50 rounded-md text-[#f85149] text-sm text-center">
            {error}
          </div>
        )}

        <div className="min-h-[120px] flex flex-col justify-center">
          {activeTab === 'github' ? (
            <RepoInput onSubmit={handleUrlSubmit} isLoading={isLoading} />
          ) : (
            <ZipUpload onSubmit={handleZipSubmit} isLoading={isLoading} />
          )}
        </div>
      </div>

      <div className="max-w-5xl mx-auto grid md:grid-cols-3 gap-8 text-center mt-8">
        <div className="flex flex-col items-center">
          <div className="w-12 h-12 rounded-full bg-[#ddf4ff] dark:bg-[#1f354a] flex items-center justify-center text-[#0969da] dark:text-[#58a6ff] mb-4">
            <GitBranch size={24} />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-[#e6edf3] mb-2">Provide</h3>
          <p className="text-gray-500 dark:text-[#8b949e]">
            Paste a GitHub URL or upload a ZIP file of your codebase.
          </p>
        </div>
        <div className="flex flex-col items-center">
          <div className="w-12 h-12 rounded-full bg-[#ddf4ff] dark:bg-[#1f354a] flex items-center justify-center text-[#0969da] dark:text-[#58a6ff] mb-4">
            <Scan size={24} />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-[#e6edf3] mb-2">Analyze</h3>
          <p className="text-gray-500 dark:text-[#8b949e]">
            We scan, parse, and index your codebase into a vector database.
          </p>
        </div>
        <div className="flex flex-col items-center">
          <div className="w-12 h-12 rounded-full bg-[#ddf4ff] dark:bg-[#1f354a] flex items-center justify-center text-[#0969da] dark:text-[#58a6ff] mb-4">
            <MessageSquare size={24} />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-[#e6edf3] mb-2">Explore</h3>
          <p className="text-gray-500 dark:text-[#8b949e]">
            Browse architecture, dependencies, and ask questions using AI.
          </p>
        </div>
      </div>
      
      <footer className="mt-auto pt-16 pb-8 text-center text-sm text-gray-400 dark:text-[#6e7681]">
        Built for developers.
      </footer>
    </div>
  )
}

export default LandingPage
