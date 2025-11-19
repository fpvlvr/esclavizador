"use client"

import { useState, useMemo, useEffect } from "react"
import { ProtectedRoute } from "@/components/protected-route"
import { Sidebar } from "@/components/sidebar"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Input } from "@/components/ui/input"
import { Calendar } from "@/components/ui/calendar"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts"
import { CalendarIcon, Download, Search, ArrowUpDown } from 'lucide-react'
import { format, startOfMonth, endOfMonth, startOfWeek, endOfWeek, subDays, subWeeks, subMonths, startOfYear } from "date-fns"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Skeleton } from "@/components/ui/skeleton"
import { useReports } from "@/hooks/use-reports"
import { useProjects } from "@/hooks/use-projects"

// Convert Date to YYYY-MM-DD format for API
const formatDateForAPI = (date: Date): string => {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

type DateRange = {
  from: Date
  to: Date
}

type PresetType = "today" | "yesterday" | "currentWeek" | "lastWeek" | "currentMonth" | "lastMonth" | "currentYear" | "allTime" | "custom"

export default function ReportsPage() {
  const [selectedProject, setSelectedProject] = useState<string>("all")
  const [searchQuery, setSearchQuery] = useState("")
  const [dateRange, setDateRange] = useState<DateRange>({
    from: startOfMonth(subMonths(new Date(), 1)),
    to: endOfMonth(subMonths(new Date(), 1)),
  })
  const [selectedPreset, setSelectedPreset] = useState<PresetType>("lastMonth")
  const [isCalendarOpen, setIsCalendarOpen] = useState(false)
  const [selectingRange, setSelectingRange] = useState<{ start: Date; end?: Date } | null>(null)

  // Fetch projects for colors and filtering
  const { projects, loading: projectsLoading } = useProjects()

  // Fetch aggregated data with date range filtering
  const { aggregates, loading: aggregatesLoading, refetch } = useReports({
    start_date: formatDateForAPI(dateRange.from),
    end_date: formatDateForAPI(dateRange.to),
  })

  // Refetch when date range changes
  useEffect(() => {
    refetch()
  }, [dateRange.from, dateRange.to, refetch])

  // Enrich aggregates with project colors
  const enrichedAggregates = useMemo(() => {
    return aggregates.map(agg => {
      const project = projects.find(p => p.id === agg.project_id)
      return {
        ...agg,
        color: project?.color || "#3b82f6",
      }
    })
  }, [aggregates, projects])

  // Calculate totals
  const totalHours = useMemo(() => {
    return enrichedAggregates.reduce((sum, project) => sum + project.total_hours, 0)
  }, [enrichedAggregates])

  const totalBillableHours = useMemo(() => {
    return enrichedAggregates.reduce((sum, project) => sum + project.billable_hours, 0)
  }, [enrichedAggregates])

  const billablePercentage = useMemo(() => {
    if (totalHours === 0) return 0
    return Math.round((totalBillableHours / totalHours) * 100)
  }, [totalHours, totalBillableHours])

  // Prepare pie chart data
  const pieChartData = useMemo(() => {
    return enrichedAggregates.map(project => ({
      name: project.project_name,
      value: project.total_hours,
      percentage: totalHours > 0 ? ((project.total_hours / totalHours) * 100).toFixed(0) : "0",
    }))
  }, [enrichedAggregates, totalHours])

  // Filter projects by search and selection
  const filteredProjects = useMemo(() => {
    return enrichedAggregates.filter(project => {
      const matchesSearch = project.project_name.toLowerCase().includes(searchQuery.toLowerCase())
      const matchesProject = selectedProject === "all" || project.project_id === selectedProject
      return matchesSearch && matchesProject
    })
  }, [enrichedAggregates, searchQuery, selectedProject])

  const handlePresetSelect = (preset: PresetType) => {
    setSelectedPreset(preset)
    const today = new Date()

    switch (preset) {
      case "today":
        setDateRange({ from: today, to: today })
        break
      case "yesterday":
        const yesterday = subDays(today, 1)
        setDateRange({ from: yesterday, to: yesterday })
        break
      case "currentWeek":
        setDateRange({ from: startOfWeek(today), to: endOfWeek(today) })
        break
      case "lastWeek":
        const lastWeekStart = startOfWeek(subWeeks(today, 1))
        const lastWeekEnd = endOfWeek(subWeeks(today, 1))
        setDateRange({ from: lastWeekStart, to: lastWeekEnd })
        break
      case "currentMonth":
        setDateRange({ from: startOfMonth(today), to: endOfMonth(today) })
        break
      case "lastMonth":
        setDateRange({
          from: startOfMonth(subMonths(today, 1)),
          to: endOfMonth(subMonths(today, 1)),
        })
        break
      case "currentYear":
        setDateRange({ from: startOfYear(today), to: today })
        break
      case "allTime":
        setDateRange({ from: new Date(2020, 0, 1), to: today })
        break
      case "custom":
        // Keep current range for custom
        break
    }

    if (preset !== "custom") {
      setIsCalendarOpen(false)
    }
  }

  const exportToCSV = () => {
    const headers = ["Project", "Hours", "Billable Hours"]
    const rows = filteredProjects.map((p) => [p.project_name, p.total_hours.toFixed(2), p.billable_hours.toFixed(2)])
    const csv = [headers, ...rows].map((row) => row.join(",")).join("\n")

    const blob = new Blob([csv], { type: "text/csv" })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `time-report-${format(dateRange.from, "yyyy-MM-dd")}-to-${format(dateRange.to, "yyyy-MM-dd")}.csv`
    a.click()
    window.URL.revokeObjectURL(url)
  }

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-background">
        <Sidebar />
        <main className="lg:pl-64">
        <div className="p-8 space-y-6">
          {/* Header with Filters */}
          <div className="flex items-center justify-between">
            <h1 className="text-3xl font-bold">Reports</h1>
            
            <Popover 
              open={isCalendarOpen} 
              onOpenChange={(open) => {
                setIsCalendarOpen(open)
                if (open) {
                  // Clear selection state when opening to start fresh
                  setSelectingRange(null)
                } else {
                  setSelectingRange(null)
                }
              }}
            >
              <PopoverTrigger asChild>
                <Button variant="outline" className="w-[280px] justify-start text-left font-normal">
                  <CalendarIcon className="mr-2 h-4 w-4" />
                  {selectedPreset === "custom" 
                    ? `${format(dateRange.from, "MMM dd, yyyy")} - ${format(dateRange.to, "MMM dd, yyyy")}`
                    : selectedPreset === "lastMonth" 
                    ? "Last Month" 
                    : selectedPreset.charAt(0).toUpperCase() + selectedPreset.slice(1).replace(/([A-Z])/g, " $1")
                  }
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-auto p-0" align="start">
                <div className="flex">
                  <div className="border-r p-3">
                    <Calendar
                      mode="single"
                      selected={selectingRange?.start || undefined}
                      onSelect={(date) => {
                        if (!date) {
                          setSelectingRange(null)
                          return
                        }

                        if (!selectingRange) {
                          // First click - start new selection
                          setSelectingRange({ start: date })
                        } else if (!selectingRange.end) {
                          // Second click - complete selection
                          const start = selectingRange.start
                          const end = date
                          const from = start < end ? start : end
                          const to = start < end ? end : start
                          setDateRange({ from, to })
                          setSelectedPreset("custom")
                          setSelectingRange(null)
                          setIsCalendarOpen(false)
                        } else {
                          // Third click - start over
                          setSelectingRange({ start: date })
                        }
                      }}
                      numberOfMonths={1}
                    />
                  </div>
                  <div className="p-2 space-y-1 flex flex-col w-[140px]">
                    <Button
                      variant={selectedPreset === "today" ? "default" : "ghost"}
                      size="sm"
                      className="justify-start h-7 px-2 text-xs whitespace-nowrap"
                      onClick={() => handlePresetSelect("today")}
                    >
                      Today
                    </Button>
                    <Button
                      variant={selectedPreset === "yesterday" ? "default" : "ghost"}
                      size="sm"
                      className="justify-start h-7 px-2 text-xs whitespace-nowrap"
                      onClick={() => handlePresetSelect("yesterday")}
                    >
                      Yesterday
                    </Button>
                    <Button
                      variant={selectedPreset === "currentWeek" ? "default" : "ghost"}
                      size="sm"
                      className="justify-start h-7 px-2 text-xs whitespace-nowrap"
                      onClick={() => handlePresetSelect("currentWeek")}
                    >
                      Current Week
                    </Button>
                    <Button
                      variant={selectedPreset === "lastWeek" ? "default" : "ghost"}
                      size="sm"
                      className="justify-start h-7 px-2 text-xs whitespace-nowrap"
                      onClick={() => handlePresetSelect("lastWeek")}
                    >
                      Last Week
                    </Button>
                    <Button
                      variant={selectedPreset === "currentMonth" ? "default" : "ghost"}
                      size="sm"
                      className="justify-start h-7 px-2 text-xs whitespace-nowrap"
                      onClick={() => handlePresetSelect("currentMonth")}
                    >
                      Current Month
                    </Button>
                    <Button
                      variant={selectedPreset === "lastMonth" ? "default" : "ghost"}
                      size="sm"
                      className="justify-start h-7 px-2 text-xs whitespace-nowrap"
                      onClick={() => handlePresetSelect("lastMonth")}
                    >
                      Last Month
                    </Button>
                    <Button
                      variant={selectedPreset === "currentYear" ? "default" : "ghost"}
                      size="sm"
                      className="justify-start h-7 px-2 text-xs whitespace-nowrap"
                      onClick={() => handlePresetSelect("currentYear")}
                    >
                      Current Year
                    </Button>
                    <Button
                      variant={selectedPreset === "allTime" ? "default" : "ghost"}
                      size="sm"
                      className="justify-start h-7 px-2 text-xs whitespace-nowrap"
                      onClick={() => handlePresetSelect("allTime")}
                    >
                      All Time
                    </Button>
                    <div className="pt-1 border-t">
                      <Button
                        variant={selectedPreset === "custom" ? "default" : "ghost"}
                        size="sm"
                        className="justify-start h-7 px-2 text-xs whitespace-nowrap"
                        onClick={() => setSelectedPreset("custom")}
                      >
                        Custom Range
                      </Button>
                    </div>
                  </div>
                </div>
              </PopoverContent>
            </Popover>
          </div>

          {/* Filters Row */}
          <div className="flex items-center gap-4">
            <Select value={selectedProject} onValueChange={setSelectedProject}>
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="Projects: All" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Projects: All</SelectItem>
                {projects.map((project) => (
                  <SelectItem key={project.id} value={project.id}>
                    <div className="flex items-center gap-2">
                      <div
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: project.color }}
                      />
                      {project.name}
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Button variant="outline" onClick={() => { setSelectedProject("all"); setSearchQuery("") }}>
              Clear Filter
            </Button>
          </div>

          {/* Summary Cards and Pie Chart */}
          <Card className="p-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Left: Summary */}
              <div>
                <div className="space-y-4 mb-6">
                  <div>
                    <p className="text-sm text-muted-foreground mb-1">Total</p>
                    <p className="text-3xl font-bold">{totalHours.toFixed(2)} h</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground mb-1">Billable</p>
                    <p className="text-2xl font-semibold">
                      {totalBillableHours.toFixed(2)} h - {billablePercentage}%
                    </p>
                  </div>
                </div>

                {/* Legend */}
                {aggregatesLoading || projectsLoading ? (
                  <div className="space-y-2">
                    {[1, 2, 3].map(i => (
                      <div key={i} className="flex items-center gap-3 animate-pulse">
                        <div className="w-4 h-4 bg-muted rounded"></div>
                        <div className="flex-1 h-4 bg-muted rounded"></div>
                        <div className="w-8 h-4 bg-muted rounded"></div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="space-y-2">
                    {pieChartData.map((entry, index) => {
                      const project = enrichedAggregates.find(p => p.project_name === entry.name)
                      return (
                        <div key={index} className="flex items-center gap-3">
                          <div
                            className="w-4 h-4 rounded"
                            style={{ backgroundColor: project?.color || "#3b82f6" }}
                          />
                          <span className="text-sm flex-1">{entry.name}</span>
                          <span className="text-sm font-medium">{entry.percentage}%</span>
                        </div>
                      )
                    })}
                  </div>
                )}
              </div>

              {/* Right: Pie Chart */}
              <div className="flex items-center justify-center">
                {aggregatesLoading || projectsLoading ? (
                  <Skeleton className="w-full h-[300px]" />
                ) : pieChartData.length === 0 ? (
                  <div className="text-center text-muted-foreground py-12">
                    <p>No data for selected period</p>
                  </div>
                ) : (
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={pieChartData}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={120}
                        dataKey="value"
                        label={({ percentage }) => `${percentage}%`}
                      >
                        {pieChartData.map((entry, index) => {
                          const project = enrichedAggregates.find(p => p.project_name === entry.name)
                          return (
                            <Cell key={`cell-${index}`} fill={project?.color || "#3b82f6"} />
                          )
                        })}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                )}
              </div>
            </div>
          </Card>

          {/* Table */}
          <Card className="p-6">
            {/* Table Controls */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <Button variant="outline" onClick={exportToCSV}>
                  <Download className="h-4 w-4 mr-2" />
                  Export to CSV
                </Button>
              </div>
              <div className="relative w-[300px]">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search"
                  className="pl-9"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
            </div>

            <div className="border rounded-lg overflow-hidden">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>
                      <button className="flex items-center gap-2 hover:text-foreground">
                        PROJECT
                        <ArrowUpDown className="h-3 w-3" />
                      </button>
                    </TableHead>
                    <TableHead className="text-right">
                      <button className="flex items-center gap-2 ml-auto hover:text-foreground">
                        HOURS
                        <ArrowUpDown className="h-3 w-3" />
                      </button>
                    </TableHead>
                    <TableHead className="text-right">
                      <button className="flex items-center gap-2 ml-auto hover:text-foreground">
                        BILLABLE HOURS
                        <ArrowUpDown className="h-3 w-3" />
                      </button>
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {aggregatesLoading || projectsLoading ? (
                    Array.from({ length: 3 }).map((_, index) => (
                      <TableRow key={index}>
                        <TableCell>
                          <div className="flex items-center gap-3">
                            <Skeleton className="w-8 h-8 rounded"></Skeleton>
                            <Skeleton className="h-4 w-32"></Skeleton>
                          </div>
                        </TableCell>
                        <TableCell className="text-right">
                          <Skeleton className="h-4 w-16 ml-auto"></Skeleton>
                        </TableCell>
                        <TableCell className="text-right">
                          <Skeleton className="h-4 w-16 ml-auto"></Skeleton>
                        </TableCell>
                      </TableRow>
                    ))
                  ) : filteredProjects.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={3} className="text-center py-8 text-muted-foreground">
                        No data for selected period
                      </TableCell>
                    </TableRow>
                  ) : (
                    filteredProjects.map((project) => (
                      <TableRow key={project.project_id}>
                        <TableCell>
                          <div className="flex items-center gap-3">
                            <div
                              className="w-8 h-8 rounded flex items-center justify-center text-white text-sm font-medium"
                              style={{ backgroundColor: project.color }}
                            >
                              {project.project_name.charAt(0)}
                            </div>
                            <span className="font-medium">{project.project_name}</span>
                          </div>
                        </TableCell>
                        <TableCell className="text-right text-primary font-medium">
                          {project.total_hours.toFixed(2)}
                        </TableCell>
                        <TableCell className="text-right text-primary font-medium">
                          {project.billable_hours.toFixed(2)}
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
          </Card>
        </div>
      </main>
    </div>
    </ProtectedRoute>
  )
}
