import axios from 'axios'
import type {
  HealthResponse,
  CreateRepositoryResponse,
  AnalysisStatus,
  AnalysisJob,
  Repository,
  RepositoryFile,
  RepositoryStats
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
): Promise<{ files: RepositoryFile[]; total: number; page: number; page_size: number }> => {
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
