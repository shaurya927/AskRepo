import React, { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { FileCode, Folder, Database, Code, ShieldAlert, FileText, Settings, Play } from 'lucide-react'
import { getRepository, getRepositoryStats, getRepositoryFiles } from '../services/api'
import type { Repository, RepositoryStats, RepositoryFile } from '../types/api'
import { formatNumber, formatBytes } from '../utils/format'
import StatsCard from '../components/StatsCard'
import LanguageBar from '../components/LanguageBar'
import FileList from '../components/FileList'
import Badge from '../components/Badge'

type TabType = 'overview' | 'files' | 'architecture' | 'dependencies' | 'history' | 'chat'

const DashboardPage: React.FC = () => {
  const { repoId } = useParams<{ repoId: string }>()
  const [activeTab, setActiveTab] = useState<TabType>('overview')
  
  const [repo, setRepo] = useState<Repository | null>(null)
  const [stats, setStats] = useState<RepositoryStats | null>(null)
  const [files, setFiles] = useState<RepositoryFile[]>([])
  
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!repoId) return

    const fetchData = async () => {
      try {
        setIsLoading(true)
        const [repoData, statsData] = await Promise.all([
          getRepository(repoId),
          getRepositoryStats(repoId)
        ])
        setRepo(repoData)
        setStats(statsData)
        
        // Also fetch initial files
        const filesData = await getRepositoryFiles(repoId, 1)
        setFiles(filesData.files)
        
        setIsLoading(false)
      } catch (err: any) {
        setError(err.message || 'Failed to load repository data')
        setIsLoading(false)
      }
    }

    fetchData()
  }, [repoId])

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center p-6">
        <div className="animate-pulse flex flex-col items-center">
          <div className="w-12 h-12 border-4 border-[#58a6ff] border-t-transparent rounded-full animate-spin mb-4" />
          <p className="text-gray-500 dark:text-[#8b949e]">Loading repository data...</p>
        </div>
      </div>
    )
  }

  if (error || !repo || !stats) {
    return (
      <div className="flex-1 p-6 flex items-center justify-center">
        <div className="text-center">
          <ShieldAlert size={48} className="mx-auto text-[#f85149] mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 dark:text-[#e6edf3] mb-2">Error Loading Repository</h2>
          <p className="text-gray-500 dark:text-[#8b949e]">{error || 'Repository not found'}</p>
        </div>
      </div>
    )
  }

  const tabs: { id: TabType; label: string; count?: number }[] = [
    { id: 'overview', label: 'Overview' },
    { id: 'files', label: 'Files', count: stats.total_files },
    { id: 'architecture', label: 'Architecture' },
    { id: 'dependencies', label: 'Dependencies' },
    { id: 'history', label: 'Git History' },
    { id: 'chat', label: 'AI Chat' }
  ]

  return (
    <div className="flex-1 flex flex-col">
      {/* Repository Header */}
      <div className="bg-white dark:bg-[#161b22] border-b border-gray-200 dark:border-[#30363d] pt-6 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center gap-3 mb-6">
            <h1 className="text-2xl font-semibold text-gray-900 dark:text-[#e6edf3] flex items-center gap-2">
              <FileCode className="text-gray-400 dark:text-[#8b949e]" />
              {repo.name}
            </h1>
            <Badge label={repo.source.toUpperCase()} variant="status" />
            {repo.url && (
              <a href={repo.url} target="_blank" rel="noopener noreferrer" className="text-sm text-[#58a6ff] hover:underline">
                View on GitHub
              </a>
            )}
          </div>
          
          <div className="flex space-x-1 overflow-x-auto">
            {tabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2 border-b-2 text-sm font-medium whitespace-nowrap transition-colors ${
                  activeTab === tab.id
                    ? 'border-[#f78166] text-gray-900 dark:text-[#e6edf3]'
                    : 'border-transparent text-gray-500 dark:text-[#8b949e] hover:text-gray-700 dark:hover:text-[#c9d1d9] hover:border-gray-300 dark:hover:border-[#8b949e]'
                }`}
              >
                {tab.label}
                {tab.count !== undefined && (
                  <span className={`px-2 py-0.5 rounded-full text-xs ${
                    activeTab === tab.id
                      ? 'bg-gray-200 dark:bg-[#30363d] text-gray-900 dark:text-[#e6edf3]'
                      : 'bg-gray-100 dark:bg-[#21262d] text-gray-500 dark:text-[#8b949e]'
                  }`}>
                    {formatNumber(tab.count)}
                  </span>
                )}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 p-6 overflow-y-auto">
        <div className="max-w-7xl mx-auto">
          
          {activeTab === 'overview' && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <StatsCard icon={FileText} label="Total Files" value={formatNumber(stats.total_files)} subtitle={`Size: ${formatBytes(stats.total_size)}`} />
                <StatsCard icon={Folder} label="Directories" value={formatNumber(stats.total_directories)} />
                <StatsCard icon={Code} label="Lines of Code" value={formatNumber(stats.total_lines)} />
                <StatsCard icon={Database} label="Languages" value={Object.keys(stats.languages).length} subtitle={`Primary: ${stats.primary_language || 'Unknown'}`} />
              </div>

              <div className="bg-white dark:bg-[#161b22] border border-gray-200 dark:border-[#30363d] rounded-lg p-6">
                <h3 className="text-lg font-medium text-gray-900 dark:text-[#e6edf3] mb-4">Languages</h3>
                <LanguageBar languages={stats.languages} totalLines={stats.total_lines} />
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-white dark:bg-[#161b22] border border-gray-200 dark:border-[#30363d] rounded-lg p-6 space-y-6">
                  <div>
                    <h3 className="text-sm font-medium text-gray-500 dark:text-[#8b949e] flex items-center gap-2 mb-3">
                      <Play size={16} /> Entry Points
                    </h3>
                    {stats.entry_points.length > 0 ? (
                      <ul className="space-y-2">
                        {stats.entry_points.map((file, i) => (
                          <li key={i} className="text-sm font-mono text-gray-700 dark:text-[#c9d1d9] bg-gray-50 dark:bg-[#0d1117] px-3 py-2 rounded-md border border-gray-100 dark:border-[#30363d]">
                            {file}
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-sm text-gray-400">No common entry points detected.</p>
                    )}
                  </div>
                  
                  <div>
                    <h3 className="text-sm font-medium text-gray-500 dark:text-[#8b949e] flex items-center gap-2 mb-3">
                      <Settings size={16} /> Configuration Files
                    </h3>
                    {stats.config_files.length > 0 ? (
                      <div className="flex flex-wrap gap-2">
                        {stats.config_files.map((file, i) => (
                          <Badge key={i} label={file} />
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-gray-400">No common config files detected.</p>
                    )}
                  </div>
                </div>

                <div className="bg-white dark:bg-[#161b22] border border-gray-200 dark:border-[#30363d] rounded-lg p-6 space-y-6">
                  <div>
                    <h3 className="text-sm font-medium text-gray-500 dark:text-[#8b949e] mb-3">Frameworks & Tools</h3>
                    {stats.frameworks.length > 0 ? (
                      <div className="flex flex-wrap gap-2">
                        {stats.frameworks.map((fw, i) => (
                          <Badge key={i} label={fw} variant="framework" />
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-gray-400">None detected.</p>
                    )}
                  </div>
                  
                  <div>
                    <h3 className="text-sm font-medium text-gray-500 dark:text-[#8b949e] mb-3">Package Managers</h3>
                    {stats.package_managers.length > 0 ? (
                      <div className="flex flex-wrap gap-2">
                        {stats.package_managers.map((pm, i) => (
                          <Badge key={i} label={pm} />
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-gray-400">None detected.</p>
                    )}
                  </div>
                  
                  <div>
                    <h3 className="text-sm font-medium text-gray-500 dark:text-[#8b949e] mb-3">Testing</h3>
                    <p className="text-gray-900 dark:text-[#e6edf3]">
                      <span className="font-semibold">{stats.test_files_count}</span> test files detected.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'files' && (
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <h2 className="text-lg font-medium text-gray-900 dark:text-[#e6edf3]">Repository Files</h2>
                <div className="text-sm text-gray-500 dark:text-[#8b949e]">
                  Showing {files.length} of {formatNumber(stats.total_files)} files
                </div>
              </div>
              <FileList files={files} />
            </div>
          )}

          {['architecture', 'dependencies', 'history', 'chat'].includes(activeTab) && (
            <div className="flex flex-col items-center justify-center py-20 bg-gray-50 dark:bg-[#0d1117] border border-dashed border-gray-300 dark:border-[#30363d] rounded-lg">
              <h3 className="text-xl font-medium text-gray-900 dark:text-[#e6edf3] mb-2 capitalize">{activeTab}</h3>
              <p className="text-gray-500 dark:text-[#8b949e]">This feature is coming in Phase 2.</p>
            </div>
          )}
          
        </div>
      </div>
    </div>
  )
}

export default DashboardPage
