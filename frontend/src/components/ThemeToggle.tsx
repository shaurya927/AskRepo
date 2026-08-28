import React from 'react'
import { Sun, Moon } from 'lucide-react'
import { useTheme } from '../hooks/useTheme'

const ThemeToggle: React.FC = () => {
  const { theme, toggleTheme } = useTheme()

  return (
    <button
      onClick={toggleTheme}
      className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-[#27272a] text-gray-600 dark:text-[#8b949e] transition-colors"
      aria-label="Toggle theme"
    >
      {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
    </button>
  )
}

export default ThemeToggle
