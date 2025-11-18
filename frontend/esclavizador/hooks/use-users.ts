import { useState, useEffect, useCallback } from 'react'
import {
  listUserStatsApiV1UsersStatsGet,
  createUserApiV1UsersPost,
  updateUserApiV1UsersUserIdPut,
  deleteUserApiV1UsersUserIdDelete,
} from '@/lib/api/generated'
import { getAuthHeaders } from '@/lib/api/client'
import type { UserStatsResponse, UserCreate, UserUpdate } from '@/lib/api/generated'
import { toast } from 'sonner'

interface UseUsersReturn {
  users: UserStatsResponse[]
  loading: boolean
  error: string | null
  createUser: (data: UserCreate) => Promise<void>
  updateUser: (id: string, data: UserUpdate) => Promise<void>
  deleteUser: (id: string) => Promise<void>
  refetch: () => Promise<void>
}

function getCurrentMonthRange() {
  const now = new Date()
  const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1)
  const endOfMonth = new Date(now.getFullYear(), now.getMonth() + 1, 0, 23, 59, 59)

  return {
    start_date: startOfMonth.toISOString().split('T')[0], // YYYY-MM-DD
    end_date: endOfMonth.toISOString().split('T')[0],
  }
}

export function useUsers(): UseUsersReturn {
  const [users, setUsers] = useState<UserStatsResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchUsers = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)

      const { start_date, end_date } = getCurrentMonthRange()

      const { data, error: apiError } = await listUserStatsApiV1UsersStatsGet({
        headers: getAuthHeaders(),
        query: {
          start_date,
          end_date,
          limit: 100,
          offset: 0,
        },
      })

      if (apiError || !data) {
        throw new Error('Failed to fetch users')
      }

      setUsers(data.items)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load users'
      setError(message)
      toast.error(message)
    } finally {
      setLoading(false)
    }
  }, [])

  const createUser = async (userData: UserCreate) => {
    try {
      const { data, error: apiError } = await createUserApiV1UsersPost({
        headers: getAuthHeaders(),
        body: userData,
      })

      if (apiError || !data) {
        throw new Error('Failed to create user')
      }

      toast.success('User created successfully')
      await fetchUsers()
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to create user'
      toast.error(message)
      throw err
    }
  }

  const updateUser = async (id: string, userData: UserUpdate) => {
    try {
      const { data, error: apiError } = await updateUserApiV1UsersUserIdPut({
        headers: getAuthHeaders(),
        path: { user_id: id },
        body: userData,
      })

      if (apiError || !data) {
        throw new Error('Failed to update user')
      }

      toast.success('User updated successfully')
      await fetchUsers()
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to update user'
      toast.error(message)
      throw err
    }
  }

  const deleteUser = async (id: string) => {
    try {
      const { error: apiError } = await deleteUserApiV1UsersUserIdDelete({
        headers: getAuthHeaders(),
        path: { user_id: id },
      })

      if (apiError) {
        throw new Error('Failed to delete user')
      }

      toast.success('User deleted successfully')
      await fetchUsers()
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to delete user'
      toast.error(message)
      throw err
    }
  }

  // Fetch users on mount
  useEffect(() => {
    fetchUsers()
  }, [fetchUsers])

  return {
    users,
    loading,
    error,
    createUser,
    updateUser,
    deleteUser,
    refetch: fetchUsers,
  }
}
