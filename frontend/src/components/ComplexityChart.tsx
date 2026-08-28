import React from 'react'

interface ComplexityChartProps {
  distribution: {
    low: number
    medium: number
    high: number
    very_high: number
  }
}

const SEGMENTS = [
  { key: 'low', label: 'Low (1-5)', color: '#3fb950' },
  { key: 'medium', label: 'Medium (6-10)', color: '#d29922' },
  { key: 'high', label: 'High (11-20)', color: '#db6d28' },
  { key: 'very_high', label: 'Very High (21+)', color: '#f85149' },
] as const

const ComplexityChart: React.FC<ComplexityChartProps> = ({ distribution }) => {
  const total = distribution.low + distribution.medium + distribution.high + distribution.very_high

  if (total === 0) {
    return (
      <div className="text-sm text-gray-400 dark:text-[#6e7681] text-center py-4">
        No complexity data available.
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {/* Stacked bar */}
      <div className="w-full h-4 rounded-full overflow-hidden flex bg-gray-200 dark:bg-[#18181b]">
        {SEGMENTS.map(({ key, color }) => {
          const value = distribution[key as keyof typeof distribution]
          const pct = (value / total) * 100
          if (pct === 0) return null
          return (
            <div
              key={key}
              style={{ width: `${pct}%`, backgroundColor: color }}
              className="h-full transition-all duration-300"
              title={`${key}: ${value} (${pct.toFixed(1)}%)`}
            />
          )
        })}
      </div>

      {/* Legend */}
      <div className="grid grid-cols-2 gap-2">
        {SEGMENTS.map(({ key, label, color }) => {
          const value = distribution[key as keyof typeof distribution]
          const pct = total > 0 ? ((value / total) * 100).toFixed(1) : '0.0'
          return (
            <div key={key} className="flex items-center gap-2 text-sm">
              <span
                className="w-3 h-3 rounded-full flex-shrink-0"
                style={{ backgroundColor: color }}
              />
              <span className="text-gray-600 dark:text-[#8b949e]">{label}</span>
              <span className="ml-auto font-medium text-gray-900 dark:text-[#e6edf3]">
                {value}
              </span>
              <span className="text-gray-400 dark:text-[#6e7681] text-xs w-12 text-right">
                {pct}%
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default ComplexityChart
