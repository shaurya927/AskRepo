import React, { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import {
  FileCode, Folder, Database, Code, ShieldAlert, FileText, Settings, Play,
  FunctionSquare, Box, Braces, Activity, GitFork, Package,
  LayoutDashboard, FolderTree, History, MessageSquare, Layers, Network
} from 'lucide-react'
import { getRepository, getRepositoryStats, getRepositoryFiles } from '../services/api'
import type { Repository, RepositoryStats, RepositoryFile } from '../types/api'
import { formatNumber, formatBytes } from '../utils/format'
import StatsCard from '../components/StatsCard'
import LanguageBar from '../components/LanguageBar'
import FileList from '../components/FileList'
import Badge from '../components/Badge'
import SymbolList from '../components/SymbolList'
import ComplexityChart from '../components/ComplexityChart'
import ChatInterface from '../components/ChatInterface'
import ArchitectureView from '../components/ArchitectureView'
import DependencyGraph from '../components/DependencyGraph'
import HistoryView from '../components/HistoryView'

type TabType = 'overview' | 'files' | 'symbols' | 'architecture' | 'dependencies' | 'history' | 'chat'

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

        const filesData = await getRepositoryFiles(repoId, 1)
        setFiles(filesData.items || [])

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

  const totalSymbols = (stats.total_functions || 0) + (stats.total_classes || 0) + (stats.total_methods || 0)

  const tabs: { id: TabType; label: string; icon: React.ElementType; count?: number }[] = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard },
    { id: 'files', label: 'Files', icon: FolderTree, count: stats.total_files },
    { id: 'symbols', label: 'Symbols', icon: Code, count: totalSymbols },
    { id: 'architecture', label: 'Architecture', icon: Layers },
    { id: 'dependencies', label: 'Dependencies', icon: Network },
    { id: 'history', label: 'Git History', icon: History },
    { id: 'chat', label: 'AI Chat', icon: MessageSquare }
  ]

  return (
    <div className="absolute inset-0 flex flex-col overflow-hidden bg-white dark:bg-[#0d1117]">
      {/* Repository Header */}
      <div className="bg-white dark:bg-[#161b22] border-b border-gray-200 dark:border-[#30363d] py-4 px-6 flex-shrink-0 z-10">
        <div className="flex items-center justify-between w-full">
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-semibold text-gray-900 dark:text-[#e6edf3] flex items-center gap-2">
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
        </div>
      </div>

      {/* Main Layout (Sidebar + Content) */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar */}
        <div className="w-64 flex-shrink-0 bg-white dark:bg-[#0d1117] border-r border-gray-200 dark:border-[#30363d] overflow-y-auto">
          <nav className="p-4 space-y-1">
            {tabs.map(tab => {
              const Icon = tab.icon
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                    activeTab === tab.id
                      ? 'bg-gray-100 dark:bg-[#1f6feb]/10 text-gray-900 dark:text-[#58a6ff]'
                      : 'text-gray-600 dark:text-[#8b949e] hover:bg-gray-50 dark:hover:bg-[#161b22] hover:text-gray-900 dark:hover:text-[#c9d1d9]'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <Icon size={18} className={activeTab === tab.id ? 'text-[#58a6ff]' : 'text-gray-400 dark:text-[#8b949e]'} />
                    <span>{tab.label}</span>
                  </div>
                  {tab.count !== undefined && (
                    <span className={`px-2 py-0.5 rounded-full text-[11px] ${
                      activeTab === tab.id
                        ? 'bg-gray-200 dark:bg-[#1f6feb]/20 text-gray-900 dark:text-[#58a6ff]'
                        : 'bg-gray-100 dark:bg-[#21262d] text-gray-500 dark:text-[#8b949e]'
                    }`}>
                      {formatNumber(tab.count)}
                    </span>
                  )}
                </button>
              )
            })}
          </nav>
        </div>

        {/* Main Content */}
        <div className={`flex-1 relative bg-white dark:bg-[#0d1117] flex flex-col ${activeTab === 'chat' ? 'overflow-hidden' : 'p-6 overflow-y-auto'}`}>
          <div className={activeTab === 'chat' ? 'flex-1 h-full' : 'max-w-7xl mx-auto w-full'}>

          {activeTab === 'overview' && (
            <div className="space-y-6">
              {/* File stats */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <StatsCard icon={FileText} label="Total Files" value={formatNumber(stats.total_files)} subtitle={`Size: ${formatBytes(stats.total_size)}`} />
                <StatsCard icon={Folder} label="Directories" value={formatNumber(stats.total_directories)} />
                <StatsCard icon={Code} label="Lines of Code" value={formatNumber(stats.total_lines)} />
                <StatsCard icon={Database} label="Languages" value={Object.keys(stats.languages).length} subtitle={`Primary: ${stats.primary_language || 'Unknown'}`} />
              </div>

              {/* Code intelligence stats */}
              {totalSymbols > 0 && (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                  <StatsCard icon={FunctionSquare} label="Functions" value={formatNumber(stats.total_functions)} />
                  <StatsCard icon={Box} label="Classes" value={formatNumber(stats.total_classes)} />
                  <StatsCard icon={Braces} label="Methods" value={formatNumber(stats.total_methods)} />
                  <StatsCard icon={Activity} label="Avg Complexity" value={stats.avg_complexity.toFixed(1)} subtitle={`Max: ${stats.max_complexity}`} />
                </div>
              )}

              {/* Languages */}
              <div className="bg-white dark:bg-[#161b22] border border-gray-200 dark:border-[#30363d] rounded-lg p-6">
                <h3 className="text-lg font-medium text-gray-900 dark:text-[#e6edf3] mb-4">Languages</h3>
                <LanguageBar languages={stats.languages} totalLines={stats.total_lines} />
              </div>

              {/* Complexity + Dependencies */}
              {totalSymbols > 0 && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div className="bg-white dark:bg-[#161b22] border border-gray-200 dark:border-[#30363d] rounded-lg p-6">
                    <h3 className="text-lg font-medium text-gray-900 dark:text-[#e6edf3] mb-4">Complexity Distribution</h3>
                    <ComplexityChart
                      distribution={{
                        low: stats.complexity_distribution?.low ?? 0,
                        medium: stats.complexity_distribution?.medium ?? 0,
                        high: stats.complexity_distribution?.high ?? 0,
                        very_high: stats.complexity_distribution?.very_high ?? 0,
                      }}
                    />
                  </div>

                  <div className="bg-white dark:bg-[#161b22] border border-gray-200 dark:border-[#30363d] rounded-lg p-6 space-y-4">
                    <h3 className="text-lg font-medium text-gray-900 dark:text-[#e6edf3] mb-4">Dependencies</h3>
                    <div className="flex items-center justify-between py-2">
                      <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-[#8b949e]">
                        <GitFork size={16} className="text-[#58a6ff]" />
                        Internal
                      </div>
                      <span className="font-semibold text-gray-900 dark:text-[#e6edf3]">{formatNumber(stats.internal_dependencies)}</span>
                    </div>
                    <div className="flex items-center justify-between py-2">
                      <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-[#8b949e]">
                        <Package size={16} className="text-[#d29922]" />
                        External
                      </div>
                      <span className="font-semibold text-gray-900 dark:text-[#e6edf3]">{formatNumber(stats.external_dependencies)}</span>
                    </div>
                  </div>
                </div>
              )}

              {/* Entry points, config, frameworks */}
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

          {activeTab === 'symbols' && (
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <h2 className="text-lg font-medium text-gray-900 dark:text-[#e6edf3]">Code Symbols</h2>
                <div className="text-sm text-gray-500 dark:text-[#8b949e]">
                  {formatNumber(totalSymbols)} symbols across {Object.keys(stats.languages).length} languages
                </div>
              </div>
              <SymbolList repoId={repoId!} />
            </div>
          )}

          {activeTab === 'chat' && (
            <ChatInterface repoId={repoId!} />
          )}

          {activeTab === 'architecture' && (
            <ArchitectureView repoId={repoId!} />
          )}

          {activeTab === 'dependencies' && (
            <DependencyGraph repoId={repoId!} />
          )}

          {activeTab === 'history' && (
            <HistoryView repoId={repoId!} />
          )}

        </div>
      </div>
    </div>
    </div>
  )
}

export default DashboardPage
