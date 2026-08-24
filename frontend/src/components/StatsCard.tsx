import React from 'react'
import type { LucideIcon } from 'lucide-react'

interface StatsCardProps {
  icon: LucideIcon
  label: string
  value: string | number
  subtitle?: string
}

const StatsCard: React.FC<StatsCardProps> = ({ icon: Icon, label, value, subtitle }) => {
  return (
    <div className="rounded-lg border border-gray-200 dark:border-[#30363d] bg-white dark:bg-[#161b22] p-4 flex flex-col transition-colors">
      <div className="flex items-center gap-2 text-gray-500 dark:text-[#8b949e] mb-2">
        <Icon size={18} />
        <span className="text-sm font-medium">{label}</span>
      </div>
      <div className="text-2xl font-semibold text-gray-900 dark:text-[#e6edf3]">
        {value}
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
