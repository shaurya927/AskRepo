import React from 'react'
import type { LanguageStats } from '../types/api'
import { getLanguageColor } from '../utils/languages'

interface LanguageBarProps {
  languages: Record<string, LanguageStats>
  totalLines: number
}

const LanguageBar: React.FC<LanguageBarProps> = ({ languages, totalLines }) => {
  const sortedLanguages = Object.entries(languages)
    .sort(([, a], [, b]) => b.lines - a.lines)
    .map(([name, stats]) => ({
      name,
      ...stats,
      percentage: totalLines > 0 ? (stats.lines / totalLines) * 100 : 0,
      color: getLanguageColor(name)
    }))

  if (sortedLanguages.length === 0) return null

  return (
    <div className="w-full space-y-3">
      <div className="h-2 w-full flex rounded-full overflow-hidden">
        {sortedLanguages.map((lang) => (
          <div
            key={lang.name}
            style={{
              width: `${lang.percentage}%`,
              backgroundColor: lang.color
            }}
            title={`${lang.name} ${lang.percentage.toFixed(1)}%`}
          />
        ))}
      </div>
      <div className="flex flex-wrap gap-x-4 gap-y-2 text-sm">
        {sortedLanguages.map((lang) => (
          <div key={lang.name} className="flex items-center gap-1.5">
            <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: lang.color }} />
            <span className="font-medium text-gray-900 dark:text-[#e6edf3]">{lang.name}</span>
            <span className="text-gray-500 dark:text-[#8b949e]">{lang.percentage.toFixed(1)}%</span>
          </div>
        ))}
      </div>
    </div>
  )
}

export default LanguageBar
