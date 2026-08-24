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
