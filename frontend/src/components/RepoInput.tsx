import React, { useState } from 'react'
import { Loader2 } from 'lucide-react'

interface RepoInputProps {
  onSubmit: (url: string) => void
  isLoading: boolean
}

const RepoInput: React.FC<RepoInputProps> = ({ onSubmit, isLoading }) => {
  const [url, setUrl] = useState('')
  const [error, setError] = useState<string | null>(null)

  const validateUrl = (val: string) => {
    if (!val) return false
    if (!val.startsWith('https://github.com/')) {
      setError('URL must start with https://github.com/')
      return false
    }
    setError(null)
    return true
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (validateUrl(url)) {
      onSubmit(url)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-xl mx-auto space-y-4">
      <div>
        <div className="flex gap-2">
          <input
            type="url"
            value={url}
            onChange={(e) => {
              setUrl(e.target.value)
              if (error) validateUrl(e.target.value)
            }}
            placeholder="https://github.com/user/repository"
            className={`flex-1 px-4 py-2 rounded-md border bg-transparent text-gray-900 dark:text-[#e6edf3] focus:outline-none focus:ring-1 focus:border-[#58a6ff] ${
              error ? 'border-[#f85149]' : 'border-gray-300 dark:border-[#27272a]'
            }`}
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !url}
            className="px-6 py-2 rounded-md bg-gray-900 hover:bg-gray-800 dark:bg-[#e6edf3] dark:hover:bg-white text-white dark:text-black font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center min-w-[100px] transition-colors"
          >
            {isLoading ? <Loader2 size={20} className="animate-spin" /> : 'Analyze'}
          </button>
        </div>
        {error && <p className="mt-2 text-sm text-[#f85149]">{error}</p>}
      </div>
    </form>
  )
}

export default RepoInput
