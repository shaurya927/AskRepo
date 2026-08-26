export interface Repository {
  id: string
  name: string
  url: string | null
  source: 'github' | 'zip'
  description: string | null
  status: 'pending' | 'analyzing' | 'completed' | 'failed'
  error_message: string | null
  created_at: string
}

export interface AnalysisJob {
  id: string
  repository_id: string
  status: 'queued' | 'cloning' | 'scanning' | 'parsing' | 'analyzing' | 'completed' | 'failed'
  progress_detail: string | null
  error_message: string | null
  started_at: string | null
  completed_at: string | null
  created_at: string
}

export interface AnalysisStatus {
  status: string
  progress_detail: string | null
  repository_id: string
}

export interface RepositoryFile {
  id: string
  path: string
  language: string | null
  size: number
  line_count: number
  is_test: boolean
  is_config: boolean
  is_entry_point: boolean
}

export interface LanguageStats {
  files: number
  lines: number
  bytes: number
}

export interface RepositoryStats {
  total_files: number
  total_directories: number
  total_lines: number
  total_size: number
  languages: Record<string, LanguageStats>
  primary_language: string | null
  frameworks: string[]
  package_managers: string[]
  entry_points: string[]
  config_files: string[]
  test_files_count: number
  total_functions: number
  total_classes: number
  total_methods: number
  avg_complexity: number
  max_complexity: number
  complexity_distribution: Record<string, number>
  internal_dependencies: number
  external_dependencies: number
}

export interface CodeSymbol {
  id: string
  repository_id: string
  file_path: string
  name: string
  symbol_type: 'function' | 'class' | 'method' | 'interface'
  language: string
  start_line: number
  end_line: number
  class_name: string | null
  signature: string | null
  docstring: string | null
  decorators: string[]
  complexity: number
}

export interface CodeImport {
  id: string
  repository_id: string
  file_path: string
  source: string
  names: string[]
  is_relative: boolean
  resolved_path: string | null
  is_internal: boolean
  line: number
}

export interface RepositoryMetrics {
  total_functions: number
  total_classes: number
  total_methods: number
  avg_complexity: number
  max_complexity: number
  complexity_distribution: {
    low: number
    medium: number
    high: number
    very_high: number
  }
  internal_dependencies: number
  external_dependencies: number
}

export interface CreateRepositoryResponse {
  repository_id: string
  job_id: string
}

export interface HealthResponse {
  status: string
  version: string
  timestamp: string
}

// Phase 3 — Chat types
export interface SourceReference {
  file_path: string
  start_line: number
  end_line: number
  symbol_name: string | null
}

export interface ChatResponse {
  id: string
  message: string
  sources: SourceReference[]
  query_category: string
  model_used: string
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources: SourceReference[] | null
  query_category: string | null
  model_used: string | null
  created_at: string
}

export interface ChatHistoryResponse {
  messages: ChatMessage[]
}

// Phase 4 — Graph & Architecture types
export interface GraphNodeData {
  label: string
  language: string
  color: string
  symbolCount: number
  nodeType: string
}

export interface GraphNode {
  id: string
  type: string
  position: { x: number; y: number }
  data: GraphNodeData
}

export interface GraphEdge {
  id: string
  source: string
  target: string
  type: string
  animated: boolean
  data: { edgeType: string }
}

export interface GraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
}

export interface NodeDetail {
  node_id: string
  node_type: string
  label: string
  language: string | null
  category: string | null
  dependencies: string[]
  dependents: string[]
  symbols: { name: string; symbol_type: string; start_line: number; end_line: number; complexity: number }[]
  symbol_count: number
}

export interface ArchitectureCategory {
  name: string
  file_count: number
  percentage: number
  sample_files: string[]
}

export interface ArchitectureResult {
  categories: Record<string, string[]>
  summary: {
    total_classified: number
    categories: ArchitectureCategory[]
  }
}

// Phase 5 — Git History types
export interface CommitSummary {
  id: string
  sha: string
  message: string
  author_name: string
  author_email: string
  authored_date: string
  committed_date: string
  files_changed: number
  insertions: number
  deletions: number
}

export interface FileChange {
  file_path: string
  change_type: string
  insertions: number
  deletions: number
  patch: string | null
}

export interface CommitDetail extends CommitSummary {
  file_changes: FileChange[]
}

export interface CommitListResponse {
  commits: CommitSummary[]
  total: number
  page: number
  per_page: number
}

export interface Hotspot {
  file_path: string
  change_count: number
  total_insertions: number
  total_deletions: number
}

export interface TimelineEntry {
  week: string
  commit_count: number
  insertions: number
  deletions: number
}

export interface CoChange {
  file_a: string
  file_b: string
  co_change_count: number
}
