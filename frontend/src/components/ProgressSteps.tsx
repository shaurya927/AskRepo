import React from 'react'
import { Check, Loader2, Circle } from 'lucide-react'

const stepsOrder = ['queued', 'cloning', 'scanning', 'parsing', 'analyzing', 'completed']
const stepLabels: Record<string, string> = {
  queued: 'Queued',
  cloning: 'Fetching Repository',
  scanning: 'Scanning Files',
  parsing: 'Parsing Codebase',
  analyzing: 'Extracting Metadata',
  completed: 'Done'
}

interface ProgressStepsProps {
  currentStatus: string
  progressDetail: string | null
}

const ProgressSteps: React.FC<ProgressStepsProps> = ({ currentStatus, progressDetail }) => {
  const currentIndex = stepsOrder.indexOf(currentStatus) === -1 ? 0 : stepsOrder.indexOf(currentStatus)

  return (
    <div className="w-full max-w-md mx-auto space-y-4">
      {stepsOrder.slice(1).map((step, index) => {
        // We slice(1) to hide "queued" if we want, or keep it. Let's keep all except queued.
        // Wait, the prompt says steps: Cloning, Scanning, Parsing, Analyzing, Complete
        // so index starts at 1
        const actualIndex = index + 1
        const isCompleted = currentIndex > actualIndex || currentStatus === 'completed'
        const isCurrent = currentStatus === step

        return (
          <div key={step} className="flex items-start gap-4">
            <div className="mt-0.5">
              {isCompleted ? (
                <Check size={20} className="text-[#3fb950]" />
              ) : isCurrent ? (
                <Loader2 size={20} className="text-[#58a6ff] animate-spin" />
              ) : (
                <Circle size={20} className="text-gray-300 dark:text-[#30363d]" />
              )}
            </div>
            <div className="flex-1">
              <h4 className={`font-medium ${isCurrent ? 'text-gray-900 dark:text-[#e6edf3]' : isCompleted ? 'text-gray-700 dark:text-[#8b949e]' : 'text-gray-400 dark:text-[#6e7681]'}`}>
                {stepLabels[step]}
              </h4>
              {isCurrent && progressDetail && (
                <p className="text-sm text-gray-500 dark:text-[#8b949e] mt-1">{progressDetail}</p>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}

export default ProgressSteps
