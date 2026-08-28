import React, { useState, useEffect, useCallback } from 'react'
import {
  ReactFlow,
  Controls,
  Background,
  MiniMap,
  useNodesState,
  useEdgesState,
  type Node,
  type Edge,
  Handle,
  Position,
  type NodeProps,
  BackgroundVariant,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { Search, Loader2, Layers, FileCode, X, ArrowRight, ArrowLeft } from 'lucide-react'
import { getRepositoryGraph, getGraphNodeDetail } from '../services/api'
import type { NodeDetail } from '../types/api'

interface DependencyGraphProps {
  repoId: string
}

// Custom node component
function FileNode({ data, selected }: NodeProps) {
  return (
    <div
      className={`px-3 py-2 rounded-lg border transition-all bg-white dark:bg-[#161b22] ${
        selected
          ? 'border-blue-500 shadow-lg shadow-blue-500/20 dark:border-[#58a6ff] dark:shadow-blue-900/20'
          : 'border-gray-200 dark:border-[#30363d] hover:border-gray-300 dark:hover:border-[#484f58]'
      } min-w-[120px]`}
    >
      <Handle type="target" position={Position.Top} className="!bg-gray-400 dark:!bg-[#30363d] !w-2 !h-2" />
      <div className="flex items-center gap-2">
        <div
          className="w-2.5 h-2.5 rounded-full flex-shrink-0"
          style={{ backgroundColor: (data as any).color || '#8b949e' }}
        />
        <span className="text-xs font-mono text-gray-900 dark:text-[#e6edf3] truncate max-w-[140px]">
          {(data as any).label}
        </span>
      </div>
      {(data as any).symbolCount > 0 && (
        <div className="text-[10px] text-gray-500 dark:text-[#8b949e] mt-1">
          {(data as any).symbolCount} {(data as any).nodeType === 'module' ? 'files' : 'symbols'}
        </div>
      )}
      <Handle type="source" position={Position.Bottom} className="!bg-gray-400 dark:!bg-[#30363d] !w-2 !h-2" />
    </div>
  )
}

const nodeTypes = { custom: FileNode }

const DependencyGraph: React.FC<DependencyGraphProps> = ({ repoId }) => {
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([])
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([])
  const [loading, setLoading] = useState(true)
  const [level, setLevel] = useState<'file' | 'module'>('file')
  const [search, setSearch] = useState('')
  const [selectedNode, setSelectedNode] = useState<NodeDetail | null>(null)
  const [loadingDetail, setLoadingDetail] = useState(false)
  
  // To observe theme changes for ReactFlow background
  const [isDark, setIsDark] = useState(document.documentElement.classList.contains('dark'))
  
  useEffect(() => {
    const observer = new MutationObserver(() => {
      setIsDark(document.documentElement.classList.contains('dark'))
    })
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] })
    return () => observer.disconnect()
  }, [])

  // Load graph data
  useEffect(() => {
    const load = async () => {
      setLoading(true)
      try {
        const data = await getRepositoryGraph(repoId, level)
        setNodes(data.nodes as unknown as Node[])
        setEdges(data.edges.map(e => ({
          ...e,
          style: { stroke: isDark ? '#30363d' : '#e5e7eb', strokeWidth: 1.5 },
          markerEnd: { type: 'arrowclosed' as any, color: isDark ? '#484f58' : '#9ca3af', width: 14, height: 14 },
        })) as unknown as Edge[])
      } catch {
        // Empty graph
        setNodes([])
        setEdges([])
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [repoId, level, setNodes, setEdges, isDark])

  // Search highlight
  useEffect(() => {
    if (!search) {
      setNodes(ns => ns.map(n => ({ ...n, style: { opacity: 1 } })))
      return
    }
    const q = search.toLowerCase()
    setNodes(ns =>
      ns.map(n => ({
        ...n,
        style: {
          opacity: n.id.toLowerCase().includes(q) || (n.data as any).label.toLowerCase().includes(q) ? 1 : 0.2,
        },
      }))
    )
  }, [search, setNodes])

  // Node click handler
  const onNodeClick = useCallback(
    async (_: any, node: Node) => {
      setLoadingDetail(true)
      try {
        const detail = await getGraphNodeDetail(repoId, node.id)
        setSelectedNode(detail)
      } catch {
        setSelectedNode(null)
      } finally {
        setLoadingDetail(false)
      }
    },
    [repoId]
  )

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="animate-spin text-gray-500 dark:text-[#8b949e]" size={24} />
        <span className="ml-2 text-gray-500 dark:text-[#8b949e]">Loading dependency graph...</span>
      </div>
    )
  }

  if (nodes.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full">
        <Layers size={48} className="text-gray-300 dark:text-[#30363d] mb-4" />
        <p className="text-gray-500 dark:text-[#8b949e]">No dependency data available for this repository.</p>
      </div>
    )
  }

  return (
    <div className="relative h-full w-full bg-white dark:bg-[#0d1117] overflow-hidden">
      {/* Toolbar */}
      <div className="absolute top-3 left-3 z-10 flex items-center gap-2">
        <div className="flex bg-white dark:bg-[#161b22] border border-gray-200 dark:border-[#30363d] rounded-lg overflow-hidden shadow-sm">
          <button
            onClick={() => setLevel('file')}
            className={`px-3 py-1.5 text-xs font-medium transition-colors ${
              level === 'file'
                ? 'bg-gray-100 dark:bg-[#21262d] text-gray-900 dark:text-[#e6edf3]'
                : 'text-gray-500 dark:text-[#8b949e] hover:text-gray-900 dark:hover:text-[#e6edf3]'
            }`}
          >
            <FileCode size={12} className="inline mr-1" /> Files
          </button>
          <button
            onClick={() => setLevel('module')}
            className={`px-3 py-1.5 text-xs font-medium transition-colors ${
              level === 'module'
                ? 'bg-gray-100 dark:bg-[#21262d] text-gray-900 dark:text-[#e6edf3]'
                : 'text-gray-500 dark:text-[#8b949e] hover:text-gray-900 dark:hover:text-[#e6edf3]'
            }`}
          >
            <Layers size={12} className="inline mr-1" /> Modules
          </button>
        </div>

        <div className="relative shadow-sm">
          <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-400 dark:text-[#6e7681]" />
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search nodes..."
            className="pl-8 pr-3 py-1.5 text-xs bg-white dark:bg-[#161b22] border border-gray-200 dark:border-[#30363d] rounded-lg text-gray-900 dark:text-[#e6edf3] placeholder-gray-400 dark:placeholder-[#6e7681] w-48 focus:border-blue-500 dark:focus:border-[#58a6ff] outline-none"
          />
        </div>

        <span className="text-xs text-gray-500 dark:text-[#6e7681] bg-white dark:bg-[#161b22] border border-gray-200 dark:border-[#30363d] rounded-lg px-2 py-1.5 shadow-sm">
          {nodes.length} nodes · {edges.length} edges
        </span>
      </div>

      {/* React Flow */}
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        nodeTypes={nodeTypes}
        fitView
        minZoom={0.1}
        maxZoom={2}
        defaultEdgeOptions={{ type: 'smoothstep' }}
      >
        <Controls className="!bg-white dark:!bg-[#161b22] !border-gray-200 dark:!border-[#30363d] [&>button]:!bg-white dark:[&>button]:!bg-[#161b22] [&>button]:!border-gray-200 dark:[&>button]:!border-[#30363d] [&>button]:!text-gray-500 dark:[&>button]:!text-[#8b949e] [&>button:hover]:!bg-gray-50 dark:[&>button:hover]:!bg-[#21262d]" />
        <Background color={isDark ? '#21262d' : '#e5e7eb'} variant={BackgroundVariant.Dots} gap={20} size={1} />
        <MiniMap
          nodeColor={n => (n.data as any)?.color || (isDark ? '#8b949e' : '#9ca3af')}
          maskColor={isDark ? 'rgba(13, 17, 23, 0.8)' : 'rgba(249, 250, 251, 0.8)'}
          className="!bg-white dark:!bg-[#161b22] !border-gray-200 dark:!border-[#30363d]"
        />
      </ReactFlow>

      {/* Node Detail Panel */}
      {(selectedNode || loadingDetail) && (
        <div className="absolute top-0 right-0 h-full w-80 bg-white dark:bg-[#161b22] border-l border-gray-200 dark:border-[#30363d] overflow-y-auto z-20 shadow-xl">
          <div className="p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-medium text-gray-900 dark:text-[#e6edf3]">Node Detail</h3>
              <button onClick={() => setSelectedNode(null)} className="text-gray-500 dark:text-[#8b949e] hover:text-gray-900 dark:hover:text-[#e6edf3]">
                <X size={16} />
              </button>
            </div>

            {loadingDetail ? (
              <Loader2 className="animate-spin text-gray-500 dark:text-[#8b949e]" size={20} />
            ) : selectedNode ? (
              <div className="space-y-4">
                <div>
                  <p className="text-xs text-gray-500 dark:text-[#8b949e] mb-1">File</p>
                  <p className="text-sm font-mono text-gray-900 dark:text-[#e6edf3] break-all">{selectedNode.node_id}</p>
                </div>

                {selectedNode.language && (
                  <div>
                    <p className="text-xs text-gray-500 dark:text-[#8b949e] mb-1">Language</p>
                    <span className="text-xs px-2 py-0.5 bg-gray-100 dark:bg-[#21262d] border border-gray-200 dark:border-[#30363d] rounded text-gray-900 dark:text-[#e6edf3]">
                      {selectedNode.language}
                    </span>
                  </div>
                )}

                {selectedNode.category && (
                  <div>
                    <p className="text-xs text-gray-500 dark:text-[#8b949e] mb-1">Architecture</p>
                    <span className="text-xs px-2 py-0.5 bg-blue-50 text-blue-600 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-800 rounded dark:text-blue-400 capitalize">
                      {selectedNode.category}
                    </span>
                  </div>
                )}

                <div>
                  <p className="text-xs text-gray-500 dark:text-[#8b949e] mb-2">
                    <ArrowRight size={12} className="inline" /> Dependencies ({selectedNode.dependencies.length})
                  </p>
                  {selectedNode.dependencies.length > 0 ? (
                    <ul className="space-y-1">
                      {selectedNode.dependencies.map(d => (
                        <li key={d} className="text-xs font-mono text-blue-600 dark:text-[#58a6ff] truncate">{d}</li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-xs text-gray-400 dark:text-[#6e7681]">None</p>
                  )}
                </div>

                <div>
                  <p className="text-xs text-gray-500 dark:text-[#8b949e] mb-2">
                    <ArrowLeft size={12} className="inline" /> Dependents ({selectedNode.dependents.length})
                  </p>
                  {selectedNode.dependents.length > 0 ? (
                    <ul className="space-y-1">
                      {selectedNode.dependents.map(d => (
                        <li key={d} className="text-xs font-mono text-blue-600 dark:text-[#58a6ff] truncate">{d}</li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-xs text-gray-400 dark:text-[#6e7681]">None</p>
                  )}
                </div>

                <div>
                  <p className="text-xs text-gray-500 dark:text-[#8b949e] mb-2">
                    Symbols ({selectedNode.symbol_count})
                  </p>
                  {selectedNode.symbols.length > 0 ? (
                    <ul className="space-y-1.5">
                      {selectedNode.symbols.map((s, i) => (
                        <li key={i} className="flex items-center justify-between text-xs">
                          <span className="font-mono text-gray-900 dark:text-[#e6edf3] truncate">{s.name}</span>
                          <span className="text-gray-400 dark:text-[#6e7681] flex-shrink-0 ml-2">{s.symbol_type}</span>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-xs text-gray-400 dark:text-[#6e7681]">None</p>
                  )}
                </div>
              </div>
            ) : null}
          </div>
        </div>
      )}
    </div>
  )
}

export default DependencyGraph
