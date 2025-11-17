"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Clock, TrendingUp, Target } from "lucide-react"

// Mock stats - will be replaced with real calculations from time entries
const mockStats = [
  {
    title: "Today's Total",
    value: "5h 15m",
    change: "+12%",
    icon: Clock,
    color: "text-chart-1",
  },
  {
    title: "This Week",
    value: "32h 45m",
    change: "+8%",
    icon: TrendingUp,
    color: "text-chart-2",
  },
  {
    title: "Weekly Goal",
    value: "82%",
    change: "33h / 40h",
    icon: Target,
    color: "text-chart-3",
  },
]

// Empty state stats - shown when no time entries exist
const emptyStats = [
  {
    title: "Today's Total",
    value: "0h 0m",
    change: "Start tracking",
    icon: Clock,
    color: "text-chart-1",
  },
  {
    title: "This Week",
    value: "0h 0m",
    change: "No entries yet",
    icon: TrendingUp,
    color: "text-chart-2",
  },
  {
    title: "Weekly Goal",
    value: "0%",
    change: "0h / 40h",
    icon: Target,
    color: "text-chart-3",
  },
]

export function Analytics() {
  // TODO: Calculate stats from real time entries
  // For now, use mock data. When time entries are empty, use emptyStats
  const hasTimeEntries = true // Will be: timeEntries.length > 0
  const stats = hasTimeEntries ? mockStats : emptyStats

  return (
    <>
      {stats.map((stat) => (
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
