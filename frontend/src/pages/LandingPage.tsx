import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { GitBranch } from 'lucide-react'
import RepoInput from '../components/RepoInput'
import ZipUpload from '../components/ZipUpload'
import { createRepositoryFromURL, createRepositoryFromZip } from '../services/api'
import ThemeToggle from '../components/ThemeToggle'
import Aurora from '../components/Aurora'
import TrueFocus from '../components/TrueFocus'
import ShinyText from '../components/ShinyText'
import SpotlightCard from '../components/SpotlightCard'
import { useTheme } from '../hooks/useTheme'

const LandingPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'github' | 'zip'>('github')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()
  const { theme } = useTheme()

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
    <div className="flex-1 flex flex-col h-full overflow-y-auto relative bg-white dark:bg-[#000000]">
      <div className="fixed inset-0 z-0 pointer-events-none opacity-30 dark:opacity-30 opacity-60">
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
      <div className="flex-1 flex flex-col items-center justify-center px-4 sm:px-6 lg:px-8 w-full relative z-10">
      <div className="text-center max-w-3xl mx-auto mb-8">
        <h1 className="text-4xl sm:text-5xl font-bold tracking-tight text-gray-900 dark:text-[#e6edf3] mb-4">
          <ShinyText 
            text="AskRepo" 
            speed={3} 
            className="inline-block" 
            color={theme === 'dark' ? '#b5b5b5' : '#475569'}
            shineColor={theme === 'dark' ? '#ffffff' : '#0f172a'}
          />
        </h1>
        <div className="text-xl sm:text-2xl font-medium text-gray-700 dark:text-[#c9d1d9] mb-4 flex justify-center">
          <TrueFocus 
            sentence="Ask your codebase anything" 
            borderColor="#58a6ff" 
            glowColor="rgba(88, 166, 255, 0.4)" 
            manualMode={false} 
            blurAmount={2}
          />
        </div>
        <p className="text-lg text-gray-500 dark:text-[#8b949e] mt-2">
          AI-powered codebase intelligence. Understand any repository in minutes.
        </p>
      </div>

      <SpotlightCard className="w-full max-w-2xl mx-auto bg-white/50 dark:bg-[#111111]/80 backdrop-blur-sm border border-gray-200 dark:border-[#27272a] rounded-xl shadow-sm p-6 mb-10" spotlightColor="rgba(88, 166, 255, 0.15)">
        <div className="flex p-1 bg-gray-100 dark:bg-[#000000] rounded-lg mb-6 max-w-sm mx-auto">
          <button
            onClick={() => setActiveTab('github')}
            className={`flex-1 py-2 text-sm font-medium rounded-md transition-all ${
              activeTab === 'github'
                ? 'bg-white dark:bg-[#18181b] text-gray-900 dark:text-[#e6edf3] shadow-sm'
                : 'text-gray-500 dark:text-[#8b949e] hover:text-gray-700 dark:hover:text-[#c9d1d9]'
            }`}
          >
            GitHub URL
          </button>
          <button
            onClick={() => setActiveTab('zip')}
            className={`flex-1 py-2 text-sm font-medium rounded-md transition-all ${
              activeTab === 'zip'
                ? 'bg-white dark:bg-[#18181b] text-gray-900 dark:text-[#e6edf3] shadow-sm'
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
      </SpotlightCard>
      
      <div className="w-full max-w-2xl mx-auto mb-8 text-center">
        <button 
          onClick={() => {
            const currentKey = localStorage.getItem('askrepo_byok_key') || '';
            const newKey = window.prompt("The public server API key allows 1500 requests/day. If you face rate limits, you can provide your own Google Gemini API key here:", currentKey);
            if (newKey !== null) {
              if (newKey.trim() === '') {
                localStorage.removeItem('askrepo_byok_key');
              } else {
                localStorage.setItem('askrepo_byok_key', newKey.trim());
              }
            }
          }}
          className="text-sm text-gray-500 hover:text-gray-900 dark:text-[#8b949e] dark:hover:text-[#c9d1d9] underline transition-colors"
        >
          Configure Custom Gemini API Key (Optional)
        </button>
      </div>

      <footer className="mt-4 mb-4 text-center text-xs text-gray-400 dark:text-[#6e7681]">
        Built for developers.
      </footer>
      </div>
    </div>
  )
}

export default LandingPage
