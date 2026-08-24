import React from 'react'
import { Link } from 'react-router-dom'
import { Terminal, GitBranch as GithubIcon } from 'lucide-react'
import ThemeToggle from './ThemeToggle'

const Header: React.FC = () => {
  return (
    <header className="sticky top-0 z-50 border-b border-gray-200 dark:border-[#30363d] bg-white dark:bg-[#0d1117]">
      <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2 text-gray-900 dark:text-[#e6edf3] hover:text-[#58a6ff] dark:hover:text-[#58a6ff] transition-colors">
          <Terminal size={24} className="text-[#58a6ff]" />
          <span className="font-semibold text-lg tracking-tight">AskRepo</span>
        </Link>
        <div className="flex items-center gap-4">
          <a
            href="https://github.com"
            target="_blank"
            rel="noopener noreferrer"
            className="text-gray-600 dark:text-[#8b949e] hover:text-gray-900 dark:hover:text-[#e6edf3] transition-colors"
          >
            <GithubIcon size={20} />
          </a>
          <ThemeToggle />
        </div>
      </div>
    </header>
  )
}

export default Header
