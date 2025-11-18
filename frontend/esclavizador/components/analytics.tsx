"use client"

import { useMemo } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Clock, TrendingUp, Target } from "lucide-react"
import { useTimeEntries } from "@/hooks/use-time-entries"

const WEEKLY_GOAL_HOURS = 40

export function Analytics() {
  // Get today's date in local timezone (YYYY-MM-DD)
  const today = useMemo(() => {
    const d = new Date()
    const year = d.getFullYear()
    const month = String(d.getMonth() + 1).padStart(2, '0')
    const day = String(d.getDate()).padStart(2, '0')
    return `${year}-${month}-${day}`
  }, [])

  // Get Monday of current week in local timezone
  const weekStart = useMemo(() => {
    const d = new Date()
    const day = d.getDay()
    const diff = d.getDate() - day + (day === 0 ? -6 : 1) // Adjust to Monday
    const monday = new Date(d.setDate(diff))
    const year = monday.getFullYear()
    const month = String(monday.getMonth() + 1).padStart(2, '0')
    const dayOfMonth = String(monday.getDate()).padStart(2, '0')
    return `${year}-${month}-${dayOfMonth}`
  }, [])

  const { entries, loading } = useTimeEntries({
    start_date: weekStart,
    is_running: false,
    limit: 100,
  })

  const stats = useMemo(() => {
    if (!entries.length) {
      return {
        todayTotal: 0,
        weekTotal: 0,
        weekGoalPercent: 0,
      }
    }

    // Convert UTC timestamps to local dates for comparison
    const todayEntries = entries.filter(e => {
      const entryDate = new Date(e.start_time)
      const year = entryDate.getFullYear()
      const month = String(entryDate.getMonth() + 1).padStart(2, '0')
      const day = String(entryDate.getDate()).padStart(2, '0')
      const localDate = `${year}-${month}-${day}`
      return localDate === today
    })

    const todayTotal = todayEntries.reduce((sum, e) => sum + (e.duration_seconds ?? 0), 0)
    const weekTotal = entries.reduce((sum, e) => sum + (e.duration_seconds ?? 0), 0)
    const weekGoalPercent = Math.round((weekTotal / (WEEKLY_GOAL_HOURS * 3600)) * 100)

    return {
      todayTotal,
      weekTotal,
      weekGoalPercent,
    }
  }, [entries, today])

  const formatDuration = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    return `${hours}h ${minutes}m`
  }

  const statCards = [
    {
      title: "Today's Total",
      value: formatDuration(stats.todayTotal),
      change: stats.todayTotal > 0 ? "Keep going!" : "Start tracking",
      icon: Clock,
      color: "text-chart-1",
    },
    {
      title: "This Week",
      value: formatDuration(stats.weekTotal),
      change: stats.weekTotal > 0 ? `${entries.length} entries` : "No entries yet",
      icon: TrendingUp,
      color: "text-chart-2",
    },
    {
      title: "Weekly Goal",
      value: `${stats.weekGoalPercent}%`,
      change: `${formatDuration(stats.weekTotal)} / ${WEEKLY_GOAL_HOURS}h`,
      icon: Target,
      color: "text-chart-3",
    },
  ]

  if (loading) {
    return (
      <>
        {[...Array(3)].map((_, i) => (
          <Card key={i} className="border-border">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-4 w-4 rounded" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-8 w-20 mb-1" />
              <Skeleton className="h-3 w-16" />
            </CardContent>
          </Card>
        ))}
      </>
    )
  }

  return (
    <>
      {statCards.map((stat) => (
        <Card key={stat.title} className="border-border">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">{stat.title}</CardTitle>
            <stat.icon className={`h-4 w-4 ${stat.color}`} />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{stat.value}</div>
            <p className="text-xs text-muted-foreground mt-1">{stat.change}</p>
          </CardContent>
        </Card>
      ))}
    </>
  )
}
