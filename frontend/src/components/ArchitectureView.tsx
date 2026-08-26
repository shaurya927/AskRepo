import React, { useState, useEffect } from 'react'
import { Loader2, FolderTree, ChevronDown, ChevronRight } from 'lucide-react'
import { getRepositoryArchitecture } from '../services/api'
import type { ArchitectureResult } from '../types/api'

interface ArchitectureViewProps {
  repoId: string
}

const CATEGORY_COLORS: Record<string, string> = {
  frontend: '#3178c6',
  backend: '#3572A5',
  api: '#e34c26',
  services: '#00ADD8',
  models: '#b07219',
  database: '#336791',
  authentication: '#f1e05a',
  tests: '#2ea44f',
  utilities: '#8b949e',
  infrastructure: '#dea584',
  config: '#6e7681',
}

const CATEGORY_ICONS: Record<string, string> = {
  frontend: '🖥',
  backend: '⚙',
  api: '🔗',
  services: '🔧',
  models: '📦',
  database: '🗄',
  authentication: '🔐',
  tests: '🧪',
  utilities: '🔨',
  infrastructure: '🏗',
  config: '⚙',
}

const ArchitectureView: React.FC<ArchitectureViewProps> = ({ repoId }) => {
  const [data, setData] = useState<ArchitectureResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [expanded, setExpanded] = useState<Set<string>>(new Set())

  useEffect(() => {
    const load = async () => {
      try {
        const result = await getRepositoryArchitecture(repoId)
        setData(result)
      } catch {
        // no data
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [repoId])

  const toggleExpand = (name: string) => {
    setExpanded(prev => {
      const next = new Set(prev)
      if (next.has(name)) next.delete(name)
      else next.add(name)
      return next
    })
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="animate-spin text-[#8b949e]" size={24} />
      </div>
    )
  }

  if (!data || data.summary.categories.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 bg-[#0d1117] border border-dashed border-[#30363d] rounded-lg">
        <FolderTree size={48} className="text-[#30363d] mb-4" />
        <p className="text-[#8b949e]">No architecture data available.</p>
      </div>
    )
  }

  const categories = data.summary.categories
  const totalFiles = data.summary.total_classified

  return (
    <div className="space-y-6">
      {/* Distribution Bar */}
      <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-4">
        <h3 className="text-sm font-medium text-[#e6edf3] mb-3">Architecture Distribution</h3>
        <div className="flex h-6 rounded-md overflow-hidden border border-[#30363d]">
          {categories.map(cat => (
            <div
              key={cat.name}
              style={{
                width: `${cat.percentage}%`,
                backgroundColor: CATEGORY_COLORS[cat.name] || '#8b949e',
                minWidth: cat.percentage > 0 ? '2px' : '0',
              }}
              title={`${cat.name}: ${cat.file_count} files (${cat.percentage}%)`}
              className="transition-all hover:opacity-80"
            />
          ))}
        </div>
        <div className="flex flex-wrap gap-3 mt-3">
          {categories.map(cat => (
            <div key={cat.name} className="flex items-center gap-1.5 text-xs text-[#8b949e]">
              <div
                className="w-2.5 h-2.5 rounded-sm"
                style={{ backgroundColor: CATEGORY_COLORS[cat.name] || '#8b949e' }}
              />
              <span className="capitalize">{cat.name}</span>
              <span className="text-[#6e7681]">{cat.percentage}%</span>
            </div>
          ))}
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-3">
          <p className="text-xs text-[#8b949e]">Total Classified</p>
          <p className="text-xl font-semibold text-[#e6edf3]">{totalFiles}</p>
        </div>
        <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-3">
          <p className="text-xs text-[#8b949e]">Categories</p>
          <p className="text-xl font-semibold text-[#e6edf3]">{categories.length}</p>
        </div>
        <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-3">
          <p className="text-xs text-[#8b949e]">Largest Layer</p>
          <p className="text-xl font-semibold text-[#e6edf3] capitalize">{categories[0]?.name || '-'}</p>
        </div>
        <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-3">
          <p className="text-xs text-[#8b949e]">Largest Count</p>
          <p className="text-xl font-semibold text-[#e6edf3]">{categories[0]?.file_count || 0}</p>
        </div>
      </div>

      {/* Category Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {categories.map(cat => {
          const allFiles = data.categories[cat.name] || []
          const isExpanded = expanded.has(cat.name)
          const displayFiles = isExpanded ? allFiles : allFiles.slice(0, 5)

          return (
            <div key={cat.name} className="bg-[#161b22] border border-[#30363d] rounded-lg overflow-hidden">
              <div className="flex items-center justify-between p-3 border-b border-[#30363d]">
                <div className="flex items-center gap-2">
                  <span className="text-base">{CATEGORY_ICONS[cat.name] || '📁'}</span>
                  <span className="text-sm font-medium text-[#e6edf3] capitalize">{cat.name}</span>
                  <span className="text-xs px-1.5 py-0.5 bg-[#21262d] border border-[#30363d] rounded text-[#8b949e]">
                    {cat.file_count}
                  </span>
                </div>
                <div
                  className="w-16 h-1.5 rounded-full bg-[#21262d] overflow-hidden"
                >
                  <div
                    className="h-full rounded-full"
                    style={{
                      width: `${cat.percentage}%`,
                      backgroundColor: CATEGORY_COLORS[cat.name] || '#8b949e',
                    }}
                  />
                </div>
              </div>
              <div className="p-3">
                <ul className="space-y-1">
                  {displayFiles.map((fp, i) => (
                    <li key={i} className="text-xs font-mono text-[#8b949e] truncate" title={fp}>
                      {fp}
                    </li>
                  ))}
                </ul>
                {allFiles.length > 5 && (
                  <button
                    onClick={() => toggleExpand(cat.name)}
                    className="flex items-center gap-1 mt-2 text-xs text-[#58a6ff] hover:underline"
                  >
                    {isExpanded ? (
                      <><ChevronDown size={12} /> Show less</>
                    ) : (
                      <><ChevronRight size={12} /> Show all {allFiles.length} files</>
                    )}
                  </button>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default ArchitectureView
