import React, { useState, useEffect } from 'react'
import { FunctionSquare, Box, Braces, Layout, ChevronDown, ChevronRight, Search } from 'lucide-react'
import { getRepositorySymbols } from '../services/api'
import type { CodeSymbol } from '../types/api'

interface SymbolListProps {
  repoId: string
}

const SymbolList: React.FC<SymbolListProps> = ({ repoId }) => {
  const [symbols, setSymbols] = useState<CodeSymbol[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [symbolType, setSymbolType] = useState<string>('')
  const [language, setLanguage] = useState<string>('')
  const [search, setSearch] = useState<string>('')
  
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set())

  const fetchSymbols = async () => {
    try {
      setIsLoading(true)
      const data = await getRepositorySymbols(repoId, page, symbolType || undefined, language || undefined, search || undefined)
      setSymbols(data.items)
      setTotal(data.total)
      setIsLoading(false)
    } catch (err: any) {
      setError(err.message || 'Failed to fetch symbols')
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchSymbols()
  }, [repoId, page, symbolType, language, search])

  const toggleExpand = (id: string) => {
    const newExpanded = new Set(expandedIds)
    if (newExpanded.has(id)) {
      newExpanded.delete(id)
    } else {
      newExpanded.add(id)
    }
    setExpandedIds(newExpanded)
  }

  const getSymbolIcon = (type: string) => {
    switch (type) {
      case 'function': return <FunctionSquare size={16} />
      case 'class': return <Box size={16} />
      case 'method': return <Braces size={16} />
      case 'interface': return <Layout size={16} />
      default: return <FunctionSquare size={16} />
    }
  }

  const getSymbolColor = (type: string) => {
    switch (type) {
      case 'function': return 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400 border-blue-200 dark:border-blue-800'
      case 'class': return 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400 border-purple-200 dark:border-purple-800'
      case 'method': return 'bg-teal-100 text-teal-800 dark:bg-teal-900/30 dark:text-teal-400 border-teal-200 dark:border-teal-800'
      case 'interface': return 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400 border-orange-200 dark:border-orange-800'
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300'
    }
  }

  const getComplexityColor = (comp: number) => {
    if (comp <= 5) return 'text-[#3fb950]'
    if (comp <= 10) return 'text-[#d29922]'
    if (comp <= 20) return 'text-[#db6d28]'
    return 'text-[#f85149]'
  }

  const truncatePath = (path: string, max = 40) => {
    if (path.length <= max) return path
    return '...' + path.slice(-(max - 3))
  }

  return (
    <div className="bg-white dark:bg-[#161b22] border border-gray-200 dark:border-[#30363d] rounded-lg overflow-hidden flex flex-col h-full">
      {/* Filter Bar */}
      <div className="p-4 border-b border-gray-200 dark:border-[#30363d] flex flex-wrap gap-4 bg-gray-50 dark:bg-[#0d1117]">
        <div className="flex-1 min-w-[200px] relative">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            placeholder="Search symbols..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            className="w-full pl-9 pr-4 py-2 bg-white dark:bg-[#161b22] border border-gray-300 dark:border-[#30363d] rounded-md text-sm text-gray-900 dark:text-[#e6edf3] focus:border-[#58a6ff] focus:ring-1 focus:ring-[#58a6ff] outline-none"
          />
        </div>
        <div className="flex gap-4">
          <div className="relative">
            <select
              value={symbolType}
              onChange={(e) => { setSymbolType(e.target.value); setPage(1); }}
              className="appearance-none pl-3 pr-8 py-2 bg-white dark:bg-[#161b22] border border-gray-300 dark:border-[#30363d] rounded-md text-sm text-gray-900 dark:text-[#e6edf3] focus:border-[#58a6ff] focus:ring-1 outline-none"
            >
              <option value="">All Types</option>
              <option value="function">Functions</option>
              <option value="class">Classes</option>
              <option value="method">Methods</option>
              <option value="interface">Interfaces</option>
            </select>
            <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 pointer-events-none" />
          </div>
          <div className="relative">
            <select
              value={language}
              onChange={(e) => { setLanguage(e.target.value); setPage(1); }}
              className="appearance-none pl-3 pr-8 py-2 bg-white dark:bg-[#161b22] border border-gray-300 dark:border-[#30363d] rounded-md text-sm text-gray-900 dark:text-[#e6edf3] focus:border-[#58a6ff] focus:ring-1 outline-none"
            >
              <option value="">All Languages</option>
              {/* Could populate from available languages in stats */}
              <option value="Python">Python</option>
              <option value="JavaScript">JavaScript</option>
              <option value="TypeScript">TypeScript</option>
              <option value="Java">Java</option>
              <option value="C++">C++</option>
              <option value="Go">Go</option>
              <option value="Rust">Rust</option>
            </select>
            <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 pointer-events-none" />
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto flex-1">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-gray-200 dark:border-[#30363d] bg-gray-50 dark:bg-[#161b22]">
              <th className="py-3 px-4 text-xs font-semibold text-gray-500 dark:text-[#8b949e] uppercase tracking-wider w-8"></th>
              <th className="py-3 px-4 text-xs font-semibold text-gray-500 dark:text-[#8b949e] uppercase tracking-wider">Name</th>
              <th className="py-3 px-4 text-xs font-semibold text-gray-500 dark:text-[#8b949e] uppercase tracking-wider">Type</th>
              <th className="py-3 px-4 text-xs font-semibold text-gray-500 dark:text-[#8b949e] uppercase tracking-wider">File</th>
              <th className="py-3 px-4 text-xs font-semibold text-gray-500 dark:text-[#8b949e] uppercase tracking-wider">Lines</th>
              <th className="py-3 px-4 text-xs font-semibold text-gray-500 dark:text-[#8b949e] uppercase tracking-wider">Complexity</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-[#30363d]">
            {isLoading && symbols.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-8 text-center text-sm text-gray-500">Loading symbols...</td>
              </tr>
            ) : error ? (
              <tr>
                <td colSpan={6} className="py-8 text-center text-sm text-red-500">{error}</td>
              </tr>
            ) : symbols.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-8 text-center text-sm text-gray-500">No symbols found.</td>
              </tr>
            ) : (
              symbols.map((symbol) => (
                <React.Fragment key={symbol.id}>
                  <tr 
                    className="hover:bg-gray-50 dark:hover:bg-[#1c2128] cursor-pointer transition-colors"
                    onClick={() => toggleExpand(symbol.id)}
                  >
                    <td className="py-3 px-4">
                      {expandedIds.has(symbol.id) ? 
                        <ChevronDown size={16} className="text-gray-400" /> : 
                        <ChevronRight size={16} className="text-gray-400" />
                      }
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-sm font-medium text-gray-900 dark:text-[#e6edf3]">
                          {symbol.name}
                        </span>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium border ${getSymbolColor(symbol.symbol_type)}`}>
                        {getSymbolIcon(symbol.symbol_type)}
                        <span className="capitalize">{symbol.symbol_type}</span>
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="font-mono text-xs text-gray-600 dark:text-[#8b949e]" title={symbol.file_path}>
                        {truncatePath(symbol.file_path)}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="font-mono text-xs text-gray-500 dark:text-[#8b949e]">
                        L{symbol.start_line}-{symbol.end_line}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className={`font-mono text-sm font-medium ${getComplexityColor(symbol.complexity)}`}>
                        {symbol.complexity}
                      </span>
                    </td>
                  </tr>
                  {expandedIds.has(symbol.id) && (
                    <tr className="bg-gray-50 dark:bg-[#0d1117] border-b border-gray-200 dark:border-[#30363d]">
                      <td colSpan={6} className="py-4 px-8">
                        <div className="space-y-4">
                          {symbol.class_name && (
                            <div className="flex gap-2 items-center text-sm">
                              <span className="text-gray-500 dark:text-[#8b949e]">Class:</span>
                              <span className="font-mono bg-gray-200 dark:bg-[#21262d] px-2 py-0.5 rounded text-gray-800 dark:text-[#c9d1d9]">
                                {symbol.class_name}
                              </span>
                            </div>
                          )}
                          
                          {symbol.decorators && symbol.decorators.length > 0 && (
                            <div className="flex gap-2 items-center flex-wrap">
                              <span className="text-sm text-gray-500 dark:text-[#8b949e]">Decorators:</span>
                              {symbol.decorators.map((dec, i) => (
                                <span key={i} className="font-mono text-xs bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400 px-2 py-0.5 rounded border border-purple-200 dark:border-purple-800">
                                  {dec}
                               </span>
                              ))}
                            </div>
                          )}

                          {symbol.signature && (
                            <div>
                              <div className="text-sm text-gray-500 dark:text-[#8b949e] mb-1">Signature</div>
                              <pre className="p-3 bg-white dark:bg-[#161b22] border border-gray-200 dark:border-[#30363d] rounded-md overflow-x-auto font-mono text-sm text-gray-800 dark:text-[#e6edf3]">
                                {symbol.signature}
                              </pre>
                            </div>
                          )}

                          {symbol.docstring && (
                            <div>
                              <div className="text-sm text-gray-500 dark:text-[#8b949e] mb-1">Docstring</div>
                              <pre className="p-3 bg-gray-100 dark:bg-[#21262d] border border-gray-200 dark:border-[#30363d] rounded-md overflow-x-auto font-mono text-sm text-green-700 dark:text-[#7ee787] whitespace-pre-wrap">
                                {symbol.docstring}
                              </pre>
                            </div>
                          )}
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {total > 0 && (
        <div className="p-4 border-t border-gray-200 dark:border-[#30363d] flex items-center justify-between bg-white dark:bg-[#161b22]">
          <div className="text-sm text-gray-500 dark:text-[#8b949e]">
            Showing {(page - 1) * 50 + 1} to {Math.min(page * 50, total)} of {total} symbols
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-3 py-1 border border-gray-300 dark:border-[#30363d] rounded-md text-sm text-gray-700 dark:text-[#c9d1d9] hover:bg-gray-50 dark:hover:bg-[#21262d] disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            <button
              onClick={() => setPage(p => p + 1)}
              disabled={page * 50 >= total}
              className="px-3 py-1 border border-gray-300 dark:border-[#30363d] rounded-md text-sm text-gray-700 dark:text-[#c9d1d9] hover:bg-gray-50 dark:hover:bg-[#21262d] disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default SymbolList
