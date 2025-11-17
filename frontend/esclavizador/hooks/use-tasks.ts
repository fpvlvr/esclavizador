import { useState, useCallback } from 'react'
import {
  listTasksApiV1TasksGet,
  createTaskApiV1TasksPost,
  updateTaskApiV1TasksTaskIdPut,
  deleteTaskApiV1TasksTaskIdDelete,
} from '@/lib/api/generated'
import { getAuthHeaders } from '@/lib/api/client'
import type { TaskResponse, TaskCreate, TaskUpdate } from '@/lib/api/generated'
import { toast } from 'sonner'

interface UseTasksReturn {
  tasks: TaskResponse[]
  loading: boolean
  error: string | null
  fetchTasks: (projectId?: string) => Promise<void>
  createTask: (data: TaskCreate) => Promise<void>
  updateTask: (id: string, data: TaskUpdate) => Promise<void>
  deleteTask: (id: string) => Promise<void>
}

export function useTasks(): UseTasksReturn {
  const [tasks, setTasks] = useState<TaskResponse[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchTasks = useCallback(async (projectId?: string) => {
    try {
      setLoading(true)
      setError(null)

      const { data, error: apiError } = await listTasksApiV1TasksGet({
        headers: getAuthHeaders(),
        query: {
          project_id: projectId,
          is_active: true,
          limit: 100,
          offset: 0,
        },
      })

      if (apiError || !data) {
        throw new Error('Failed to fetch tasks')
      }

      setTasks(data.items)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load tasks'
      setError(message)
      toast.error(message)
    } finally {
      setLoading(false)
    }
  }, [])

  const createTask = async (taskData: TaskCreate) => {
    try {
      const { data, error: apiError } = await createTaskApiV1TasksPost({
        headers: getAuthHeaders(),
        body: taskData,
      })

      if (apiError || !data) {
        throw new Error('Failed to create task')
      }

      toast.success('Task created successfully')
      // Note: Caller should refetch tasks for the project
      await fetchTasks(data.project_id)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to create task'
      toast.error(message)
      throw err
    }
  }

  const updateTask = async (id: string, taskData: TaskUpdate) => {
    try {
      const { data, error: apiError } = await updateTaskApiV1TasksTaskIdPut({
        headers: getAuthHeaders(),
        path: { task_id: id },
        body: taskData,
      })

      if (apiError || !data) {
        throw new Error('Failed to update task')
      }

      toast.success('Task updated successfully')
      // Update the task in the local state
      setTasks(prev => prev.map(task => task.id === id ? data : task))
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to update task'
      toast.error(message)
      throw err
    }
  }

  const deleteTask = async (id: string) => {
    try {
      const { error: apiError } = await deleteTaskApiV1TasksTaskIdDelete({
        headers: getAuthHeaders(),
        path: { task_id: id },
      })

      if (apiError) {
        throw new Error('Failed to delete task')
      }

      toast.success('Task deleted successfully')
      // Remove the task from local state
      setTasks(prev => prev.filter(task => task.id !== id))
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to delete task'
      toast.error(message)
      throw err
    }
  }

  return {
    tasks,
    loading,
    error,
    fetchTasks,
    createTask,
    updateTask,
    deleteTask,
  }
}
