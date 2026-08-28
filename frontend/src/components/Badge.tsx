import React from 'react'
import { getLanguageColor } from '../utils/languages'

interface BadgeProps {
  label: string
  color?: string
  variant?: 'language' | 'framework' | 'status' | 'default'
}

const Badge: React.FC<BadgeProps> = ({ label, color, variant = 'default' }) => {
  if (variant === 'language') {
    const langColor = color || getLanguageColor(label)
    return (
      <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium border border-gray-200 dark:border-[#27272a] bg-white dark:bg-[#18181b] text-gray-700 dark:text-[#c9d1d9]">
        <div className="w-2 h-2 rounded-full" style={{ backgroundColor: langColor }} />
        {label}
      </span>
    )
  }

  if (variant === 'framework') {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium bg-[#ddf4ff] dark:bg-[#1f354a] text-[#0969da] dark:text-[#79c0ff]">
        {label}
      </span>
    )
  }
  
  if (variant === 'status') {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border border-gray-200 dark:border-[#27272a] bg-gray-50 dark:bg-[#111111] text-gray-600 dark:text-[#8b949e]">
        {label}
      </span>
    )
  }

  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 dark:bg-[#27272a] text-gray-800 dark:text-[#e6edf3]">
      {label}
    </span>
  )
}

export default Badge
