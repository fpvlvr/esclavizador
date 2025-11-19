import { useState, useEffect, useCallback } from 'react'
import { toast } from 'sonner'
import { getProjectAggregatesApiV1ReportsProjectsGet } from '@/lib/api/generated'
import { getAuthHeaders } from '@/lib/api/client'
import type { ProjectAggregate } from '@/lib/api/generated'

interface UseReportsFilters {
  start_date?: string | null
  end_date?: string | null
  user_id?: string | null
}

interface UseReportsReturn {
  aggregates: ProjectAggregate[]
  loading: boolean
  error: string | null
  refetch: () => Promise<void>
}

export function useReports(filters?: UseReportsFilters): UseReportsReturn {
  const [aggregates, setAggregates] = useState<ProjectAggregate[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchAggregates = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)

      const { data, error: apiError } = await getProjectAggregatesApiV1ReportsProjectsGet({
        headers: getAuthHeaders(),
        query: {
          start_date: filters?.start_date || null,
          end_date: filters?.end_date || null,
          user_id: filters?.user_id || null,
        },
      })

      if (apiError || !data) {
        console.warn('Failed to fetch project aggregates:', apiError)
        setError('Failed to fetch reports data')
        setAggregates([])
        return
      }

      setAggregates(data.items ?? [])
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch reports data'
      setError(message)
      console.error('Error fetching project aggregates:', err)
      setAggregates([])
    } finally {
      setLoading(false)
    }
  }, [filters?.start_date, filters?.end_date, filters?.user_id])

  useEffect(() => {
    fetchAggregates()
  }, [fetchAggregates])

  return {
    aggregates,
    loading,
    error,
    refetch: fetchAggregates,
  }
}

