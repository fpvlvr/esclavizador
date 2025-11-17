import { useState, useEffect, useCallback } from 'react'
import {
  listProjectsApiV1ProjectsGet,
  createProjectApiV1ProjectsPost,
  updateProjectApiV1ProjectsProjectIdPut,
  deleteProjectApiV1ProjectsProjectIdDelete,
} from '@/lib/api/generated'
import { getAuthHeaders } from '@/lib/api/client'
import type { ProjectResponse, ProjectCreate, ProjectUpdate } from '@/lib/api/generated'
import { toast } from 'sonner'

interface UseProjectsReturn {
  projects: ProjectResponse[]
  loading: boolean
  error: string | null
  createProject: (data: ProjectCreate) => Promise<void>
  updateProject: (id: string, data: ProjectUpdate) => Promise<void>
  deleteProject: (id: string) => Promise<void>
  refetch: () => Promise<void>
}

export function useProjects(): UseProjectsReturn {
  const [projects, setProjects] = useState<ProjectResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchProjects = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)

      const { data, error: apiError } = await listProjectsApiV1ProjectsGet({
        headers: getAuthHeaders(),
        query: {
          is_active: true,
          limit: 100,
          offset: 0,
        },
      })

      if (apiError || !data) {
        throw new Error('Failed to fetch projects')
      }

      setProjects(data.items)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load projects'
      setError(message)
      toast.error(message)
    } finally {
      setLoading(false)
    }
  }, [])

  const createProject = async (projectData: ProjectCreate) => {
    try {
      const { data, error: apiError } = await createProjectApiV1ProjectsPost({
        headers: getAuthHeaders(),
        body: projectData,
      })

      if (apiError || !data) {
        throw new Error('Failed to create project')
      }

      toast.success('Project created successfully')
      await fetchProjects() // Refetch to get updated list
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to create project'
      toast.error(message)
      throw err
    }
  }

  const updateProject = async (id: string, projectData: ProjectUpdate) => {
    try {
      const { data, error: apiError } = await updateProjectApiV1ProjectsProjectIdPut({
        headers: getAuthHeaders(),
        path: { project_id: id },
        body: projectData,
      })

      if (apiError || !data) {
        throw new Error('Failed to update project')
      }

      toast.success('Project updated successfully')
      await fetchProjects() // Refetch to get updated list
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to update project'
      toast.error(message)
      throw err
    }
  }

  const deleteProject = async (id: string) => {
    try {
      const { error: apiError } = await deleteProjectApiV1ProjectsProjectIdDelete({
        headers: getAuthHeaders(),
        path: { project_id: id },
      })

      if (apiError) {
        throw new Error('Failed to delete project')
      }

      toast.success('Project deleted successfully')
      await fetchProjects() // Refetch to get updated list
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to delete project'
      toast.error(message)
      throw err
    }
  }

  // Fetch projects on mount
  useEffect(() => {
    fetchProjects()
  }, [fetchProjects])

  return {
    projects,
    loading,
    error,
    createProject,
    updateProject,
    deleteProject,
    refetch: fetchProjects,
  }
}
