import React from 'react'
import type { LucideIcon } from 'lucide-react'
import CountUp from './CountUp'

interface StatsCardProps {
  icon: LucideIcon
  label: string
  value: string | number
  subtitle?: string
}

const StatsCard: React.FC<StatsCardProps> = ({ icon: Icon, label, value, subtitle }) => {
  const numericValue = typeof value === 'string' ? parseFloat(value.replace(/,/g, '')) : value
  const isNumeric = !isNaN(numericValue)

  return (
    <div className="rounded-lg border border-gray-200 dark:border-[#27272a] bg-white dark:bg-[#111111] p-4 flex flex-col transition-all duration-300 hover:-translate-y-1 hover:shadow-lg dark:hover:shadow-white/5 hover:border-gray-300 dark:hover:border-gray-600">
      <div className="flex items-center gap-2 text-gray-500 dark:text-[#8b949e] mb-2">
        <Icon size={18} />
        <span className="text-sm font-medium">{label}</span>
      </div>
      <div className="text-2xl font-semibold text-gray-900 dark:text-[#e6edf3]">
        {isNumeric ? (
          <CountUp to={numericValue} duration={1.5} separator="," />
        ) : (
          value
        )}
      </div>
      {subtitle && (
        <div className="mt-1 text-xs text-gray-400 dark:text-[#6e7681]">
          {subtitle}
        </div>
      )}
    </div>
  )
}

export default StatsCard
