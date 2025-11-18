import { useState, useEffect, useCallback } from 'react'
import { toast } from 'sonner'
import {
  listTimeEntriesApiV1TimeEntriesGet,
  createManualEntryApiV1TimeEntriesPost,
  updateTimeEntryApiV1TimeEntriesEntryIdPut,
  deleteTimeEntryApiV1TimeEntriesEntryIdDelete,
} from '@/lib/api/generated'
import { getAuthHeaders } from '@/lib/api/client'
import type { TimeEntryResponse, TimeEntryCreate, TimeEntryUpdate } from '@/lib/api/generated'

interface TimeEntriesFilters {
  project_id?: string | null
  task_id?: string | null
  is_billable?: boolean | null
  user_id?: string | null
  start_date?: string | null
  end_date?: string | null
  is_running?: boolean | null
  tag_ids?: string[] | null
  limit?: number
  offset?: number
}

interface UseTimeEntriesReturn {
  entries: TimeEntryResponse[]
  total: number
  loading: boolean
  error: string | null
  createEntry: (data: TimeEntryCreate) => Promise<void>
  updateEntry: (entryId: string, data: TimeEntryUpdate) => Promise<void>
  deleteEntry: (entryId: string) => Promise<void>
  refetch: () => Promise<void>
  setFilters: (filters: TimeEntriesFilters) => void
}

export function useTimeEntries(initialFilters?: TimeEntriesFilters): UseTimeEntriesReturn {
  const [entries, setEntries] = useState<TimeEntryResponse[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filters, setFilters] = useState<TimeEntriesFilters>(initialFilters ?? { limit: 50, offset: 0 })

  // Update filters when initialFilters change
  useEffect(() => {
    if (initialFilters) {
      setFilters(initialFilters)
    }
  }, [initialFilters?.start_date, initialFilters?.end_date, initialFilters?.project_id, initialFilters?.task_id, initialFilters?.is_billable, initialFilters?.user_id, initialFilters?.is_running, initialFilters?.limit, initialFilters?.offset])

  // Fetch time entries
  const fetchEntries = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)

      const { data, error: apiError } = await listTimeEntriesApiV1TimeEntriesGet({
        headers: getAuthHeaders(),
        query: filters,
      })

      if (apiError || !data) {
        console.warn('Failed to fetch time entries:', apiError)
        setError('Failed to fetch time entries')
        setEntries([])
        setTotal(0)
        return
      }

      setEntries(data.items ?? [])
      setTotal(data.total ?? 0)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch time entries'
      setError(message)
      console.error('Error fetching time entries:', err)
      // Set empty data on error to prevent UI crashes
      setEntries([])
      setTotal(0)
    } finally {
      setLoading(false)
    }
  }, [filters])

  // Create manual entry
  const createEntry = async (data: TimeEntryCreate) => {
    try {
      setError(null)

      const { data: newEntry, error: apiError } = await createManualEntryApiV1TimeEntriesPost({
        headers: getAuthHeaders(),
        body: data,
      })

      if (apiError || !newEntry) {
        throw new Error('Failed to create time entry')
      }

      toast.success('Time entry created successfully')
      await fetchEntries()
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to create time entry'
      setError(message)
      toast.error(message)
      throw err
    }
  }

  // Update entry
  const updateEntry = async (entryId: string, data: TimeEntryUpdate) => {
    try {
      setError(null)

      const { data: updatedEntry, error: apiError } = await updateTimeEntryApiV1TimeEntriesEntryIdPut({
        headers: getAuthHeaders(),
        path: { entry_id: entryId },
        body: data,
      })

      if (apiError || !updatedEntry) {
        throw new Error('Failed to update time entry')
      }

      toast.success('Time entry updated successfully')
      await fetchEntries()
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to update time entry'
      setError(message)
      toast.error(message)
      throw err
    }
  }

  // Delete entry
  const deleteEntry = async (entryId: string) => {
    try {
      setError(null)

      const { error: apiError } = await deleteTimeEntryApiV1TimeEntriesEntryIdDelete({
        headers: getAuthHeaders(),
        path: { entry_id: entryId },
      })

      if (apiError) {
        throw new Error('Failed to delete time entry')
      }

      toast.success('Time entry deleted successfully')
      await fetchEntries()
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to delete time entry'
      setError(message)
      toast.error(message)
      throw err
    }
  }

  // Fetch entries on mount and when filters change
  useEffect(() => {
    fetchEntries()
  }, [fetchEntries])

  return {
    entries,
    total,
    loading,
    error,
    createEntry,
    updateEntry,
    deleteEntry,
    refetch: fetchEntries,
    setFilters,
  }
}
