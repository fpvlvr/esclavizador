import { useState, useEffect, useCallback } from 'react'
import { toast } from 'sonner'
import {
  startTimerApiV1TimeEntriesStartPost,
  stopTimerApiV1TimeEntriesEntryIdStopPost,
  getRunningTimerApiV1TimeEntriesRunningGet,
} from '@/lib/api/generated'
import { getAuthHeaders } from '@/lib/api/client'
import type { TimeEntryResponse, TimeEntryStart } from '@/lib/api/generated'

interface UseTimerReturn {
  runningEntry: TimeEntryResponse | null
  elapsedSeconds: number
  isRunning: boolean
  loading: boolean
  error: string | null
  startTimer: (data: TimeEntryStart) => Promise<void>
  stopTimer: () => Promise<void>
  refetch: () => Promise<void>
}

const STORAGE_KEY = 'running_timer'

export function useTimer(): UseTimerReturn {
  const [runningEntry, setRunningEntry] = useState<TimeEntryResponse | null>(null)
  const [elapsedSeconds, setElapsedSeconds] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const isRunning = runningEntry?.is_running ?? false

  // Fetch running timer from backend
  const fetchRunningTimer = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)

      const { data, error: apiError } = await getRunningTimerApiV1TimeEntriesRunningGet({
        headers: getAuthHeaders(),
      })

      if (apiError) {
        console.warn('Failed to fetch running timer:', apiError)
        // Don't throw error, just set null - this is not critical
        setRunningEntry(null)
        setElapsedSeconds(0)
        localStorage.removeItem(STORAGE_KEY)
        return
      }

      setRunningEntry(data ?? null)

      // Calculate elapsed time if timer is running
      if (data?.is_running && data.start_time) {
        const startTime = new Date(data.start_time).getTime()
        const now = Date.now()
        const elapsed = Math.floor((now - startTime) / 1000)
        setElapsedSeconds(elapsed)

        // Save to localStorage
        localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
      } else {
        // Clear localStorage if no running timer
        localStorage.removeItem(STORAGE_KEY)
        setElapsedSeconds(0)
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch running timer'
      setError(message)
      console.error('Error fetching running timer:', err)
      // Set safe defaults on error
      setRunningEntry(null)
      setElapsedSeconds(0)
      localStorage.removeItem(STORAGE_KEY)
    } finally {
      setLoading(false)
    }
  }, [])

  // Start timer
  const startTimer = async (data: TimeEntryStart) => {
    try {
      setError(null)

      const { data: newEntry, error: apiError } = await startTimerApiV1TimeEntriesStartPost({
        headers: getAuthHeaders(),
        body: data,
      })

      if (apiError || !newEntry) {
        throw new Error('Failed to start timer')
      }

      setRunningEntry(newEntry)
      setElapsedSeconds(0)

      // Save to localStorage
      localStorage.setItem(STORAGE_KEY, JSON.stringify(newEntry))

      toast.success('Timer started')
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to start timer'
      setError(message)
      toast.error(message)
      throw err
    }
  }

  // Stop timer
  const stopTimer = async () => {
    if (!runningEntry) {
      toast.error('No running timer to stop')
      return
    }

    try {
      setError(null)

      const { data: stoppedEntry, error: apiError } = await stopTimerApiV1TimeEntriesEntryIdStopPost({
        headers: getAuthHeaders(),
        path: { entry_id: runningEntry.id },
      })

      if (apiError || !stoppedEntry) {
        throw new Error('Failed to stop timer')
      }

      setRunningEntry(null)
      setElapsedSeconds(0)

      // Clear localStorage
      localStorage.removeItem(STORAGE_KEY)

      toast.success(`Timer stopped - ${formatDuration(stoppedEntry.duration_seconds ?? 0)}`)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to stop timer'
      setError(message)
      toast.error(message)
      throw err
    }
  }

  // Tick timer every second when running
  useEffect(() => {
    if (!isRunning) return

    const interval = setInterval(() => {
      setElapsedSeconds((prev) => prev + 1)
    }, 1000)

    return () => clearInterval(interval)
  }, [isRunning])

  // Fetch running timer on mount
  useEffect(() => {
    fetchRunningTimer()
  }, [fetchRunningTimer])

  // Restore timer from localStorage on mount (backup if API is slow)
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      try {
        const entry = JSON.parse(stored) as TimeEntryResponse
        if (entry.is_running) {
          setRunningEntry(entry)
          // Calculate elapsed time
          const startTime = new Date(entry.start_time).getTime()
          const now = Date.now()
          const elapsed = Math.floor((now - startTime) / 1000)
          setElapsedSeconds(elapsed)
        }
      } catch (err) {
        console.error('Error restoring timer from localStorage:', err)
        localStorage.removeItem(STORAGE_KEY)
      }
    }
  }, [])

  return {
    runningEntry,
    elapsedSeconds,
    isRunning,
    loading,
    error,
    startTimer,
    stopTimer,
    refetch: fetchRunningTimer,
  }
}

function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  return `${hours}h ${minutes}m`
}
