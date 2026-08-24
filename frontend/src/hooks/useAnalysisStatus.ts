import { useState, useEffect } from 'react'
import { getAnalysisStatus } from '../services/api'
import type { AnalysisStatus } from '../types/api'

export const useAnalysisStatus = (jobId: string | undefined) => {
  const [status, setStatus] = useState<string>('queued')
  const [progressDetail, setProgressDetail] = useState<string | null>(null)
  const [repositoryId, setRepositoryId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isComplete, setIsComplete] = useState<boolean>(false)
  const [isFailed, setIsFailed] = useState<boolean>(false)

  useEffect(() => {
    if (!jobId) return

    let intervalId: ReturnType<typeof setInterval>
    let isActive = true

    const fetchStatus = async () => {
      try {
        const data: AnalysisStatus = await getAnalysisStatus(jobId)
        if (!isActive) return

        setStatus(data.status)
        setProgressDetail(data.progress_detail)
        
        if (data.repository_id) {
          setRepositoryId(data.repository_id)
        }

        if (data.status === 'completed') {
          setIsComplete(true)
          clearInterval(intervalId)
        } else if (data.status === 'failed') {
          setIsFailed(true)
          clearInterval(intervalId)
        }
      } catch (err: any) {
        if (!isActive) return
        setError(err.message || 'Failed to fetch status')
        setIsFailed(true)
        clearInterval(intervalId)
      }
    }

    fetchStatus()
    intervalId = setInterval(fetchStatus, 2000)

    return () => {
      isActive = false
      clearInterval(intervalId)
    }
  }, [jobId])

  return { status, progressDetail, repositoryId, isComplete, isFailed, error }
}
