import axios from 'axios'
import type {
  HealthResponse,
  CreateRepositoryResponse,
  AnalysisStatus,
  AnalysisJob,
  Repository,
  RepositoryFile,
  RepositoryStats,
  CodeSymbol,
  CodeImport,
  RepositoryMetrics,
  ChatResponse,
  ChatHistoryResponse,
  GraphData,
  NodeDetail,
  ArchitectureResult,
  CommitListResponse,
  CommitDetail,
  Hotspot,
  TimelineEntry,
  CoChange,
} from '../types/api'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
})

export const checkHealth = async (): Promise<HealthResponse> => {
  const response = await api.get('/health')
  return response.data
}

export const createRepositoryFromURL = async (url: string): Promise<CreateRepositoryResponse> => {
  const formData = new FormData()
  formData.append('url', url)
  const response = await api.post('/repositories/from-url', formData)
  return response.data
}

export const createRepositoryFromZip = async (file: File): Promise<CreateRepositoryResponse> => {
  const formData = new FormData()
  formData.append('file', file)
  const response = await api.post('/repositories/from-zip', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return response.data
}

export const getAnalysisStatus = async (jobId: string): Promise<AnalysisStatus> => {
  const response = await api.get(`/analyses/${jobId}/status`)
  return response.data
}

export const getAnalysisJob = async (jobId: string): Promise<AnalysisJob> => {
  const response = await api.get(`/analyses/${jobId}`)
  return response.data
}

export const getRepository = async (repoId: string): Promise<Repository> => {
  const response = await api.get(`/repositories/${repoId}`)
  return response.data
}

export const getRepositoryFiles = async (
  repoId: string,
  page: number = 1,
  language?: string
): Promise<{ items: RepositoryFile[]; total: number; page: number; size: number }> => {
  const params: Record<string, string | number> = { page }
  if (language) {
    params.language = language
  }
  const response = await api.get(`/repositories/${repoId}/files`, { params })
  return response.data
}

export const getRepositoryStats = async (repoId: string): Promise<RepositoryStats> => {
  const response = await api.get(`/repositories/${repoId}/stats`)
  return response.data
}

export const getRepositorySymbols = async (
  repoId: string,
  page: number = 1,
  symbolType?: string,
  language?: string,
  search?: string
): Promise<{ items: CodeSymbol[]; total: number; page: number; size: number }> => {
  const params: Record<string, string | number> = { page }
  if (symbolType) params.symbol_type = symbolType
  if (language) params.language = language
  if (search) params.search = search
  const response = await api.get(`/repositories/${repoId}/symbols`, { params })
  return response.data
}

export const getRepositoryImports = async (
  repoId: string,
  isInternal?: boolean
): Promise<{ items: CodeImport[]; total: number }> => {
  const params: Record<string, any> = {}
  if (isInternal !== undefined) params.is_internal = isInternal
  const response = await api.get(`/repositories/${repoId}/imports`, { params })
  return response.data
}

export const getRepositoryMetrics = async (
  repoId: string
): Promise<RepositoryMetrics> => {
  const response = await api.get(`/repositories/${repoId}/metrics`)
  return response.data
}

// Phase 3 — Chat API
export const sendChatMessage = async (
  repoId: string,
  message: string,
  apiKey?: string,
  signal?: AbortSignal
): Promise<ChatResponse> => {
  const response = await api.post(`/repositories/${repoId}/chat`, {
    message,
    api_key: apiKey || undefined,
  }, { signal })
  
  const data = response.data as ChatResponse
  
  if (response.headers['x-ratelimit-limit'] && response.headers['x-ratelimit-remaining']) {
    data.rate_limit = {
      limit: parseInt(response.headers['x-ratelimit-limit'], 10),
      remaining: parseInt(response.headers['x-ratelimit-remaining'], 10),
    }
  }
  
  return data
}

export const getChatHistory = async (
  repoId: string
): Promise<ChatHistoryResponse> => {
  const response = await api.get(`/repositories/${repoId}/chat/history`)
  return response.data
}

// Phase 4 — Graph & Architecture API
export const getRepositoryGraph = async (
  repoId: string,
  level: string = 'file',
  language?: string
): Promise<GraphData> => {
  const params: Record<string, string> = { level }
  if (language) params.language = language
  const response = await api.get(`/repositories/${repoId}/graph`, { params })
  return response.data
}

export const getGraphNodeDetail = async (
  repoId: string,
  nodeId: string
): Promise<NodeDetail> => {
  const response = await api.get(`/repositories/${repoId}/graph/node/${encodeURIComponent(nodeId)}`)
  return response.data
}

export const getRepositoryArchitecture = async (
  repoId: string
): Promise<ArchitectureResult> => {
  const response = await api.get(`/repositories/${repoId}/architecture`)
  return response.data
}

// Phase 5 — Git History API
export const getCommits = async (
  repoId: string,
  page: number = 1,
  perPage: number = 50,
  filePath?: string
): Promise<CommitListResponse> => {
  const params: Record<string, string | number> = { page, per_page: perPage }
  if (filePath) params.file_path = filePath
  const response = await api.get(`/repositories/${repoId}/commits`, { params })
  return response.data
}

export const getCommitDetail = async (
  repoId: string,
  sha: string
): Promise<CommitDetail> => {
  const response = await api.get(`/repositories/${repoId}/commits/${sha}`)
  return response.data
}

export const getHotspots = async (
  repoId: string
): Promise<{ hotspots: Hotspot[] }> => {
  const response = await api.get(`/repositories/${repoId}/history/hotspots`)
  return response.data
}

export const getTimeline = async (
  repoId: string
): Promise<{ timeline: TimelineEntry[] }> => {
  const response = await api.get(`/repositories/${repoId}/history/timeline`)
  return response.data
}

export const getCoChanges = async (
  repoId: string
): Promise<{ co_changes: CoChange[] }> => {
  const response = await api.get(`/repositories/${repoId}/history/co-changes`)
  return response.data
}
