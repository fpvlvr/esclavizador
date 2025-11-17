"use client"

import { useState } from "react"
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
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from "recharts"
import { CalendarIcon, Download, Search, ArrowUpDown } from 'lucide-react'
import { cn } from "@/lib/utils"
import { format, startOfMonth, endOfMonth, startOfWeek, endOfWeek, subDays, subWeeks, subMonths, startOfYear } from "date-fns"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

// Mock data for projects
const projectsData = [
  { name: "Website Redesign", hours: 42.5, billableHours: 42.5, color: "#3b82f6" },
  { name: "Mobile App Development", hours: 68.25, billableHours: 68.25, color: "#f59e0b" },
  { name: "API Integration", hours: 28.75, billableHours: 28.75, color: "#10b981" },
  { name: "Marketing Campaign", hours: 15.33, billableHours: 15.33, color: "#ef4444" },
]

const tags = ["Frontend", "Backend", "Design", "Marketing", "DevOps"]

type DateRange = {
  from: Date
  to: Date
}

type PresetType = "today" | "yesterday" | "currentWeek" | "lastWeek" | "currentMonth" | "lastMonth" | "currentYear" | "allTime" | "custom"

export default function ReportsPage() {
  const [selectedProject, setSelectedProject] = useState<string>("all")
  const [selectedTag, setSelectedTag] = useState<string>("all")
  const [searchQuery, setSearchQuery] = useState("")
  const [dateRange, setDateRange] = useState<DateRange>({
    from: startOfMonth(subMonths(new Date(), 1)),
    to: endOfMonth(subMonths(new Date(), 1)),
  })
  const [selectedPreset, setSelectedPreset] = useState<PresetType>("lastMonth")
  const [isCalendarOpen, setIsCalendarOpen] = useState(false)

  const totalHours = projectsData.reduce((sum, project) => sum + project.hours, 0)
  const totalBillableHours = projectsData.reduce((sum, project) => sum + project.billableHours, 0)

  const pieChartData = projectsData.map((project) => ({
    name: project.name,
    value: project.hours,
    percentage: ((project.hours / totalHours) * 100).toFixed(0),
  }))

  const filteredProjects = projectsData.filter((project) => {
    const matchesSearch = project.name.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesProject = selectedProject === "all" || project.name === selectedProject
    return matchesSearch && matchesProject
  })

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
    const rows = filteredProjects.map((p) => [p.name, p.hours.toFixed(2), p.billableHours.toFixed(2)])
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
            
            <Popover open={isCalendarOpen} onOpenChange={setIsCalendarOpen}>
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
                      mode="range"
                      selected={{ from: dateRange.from, to: dateRange.to }}
                      onSelect={(range) => {
                        if (range?.from && range?.to) {
                          setDateRange({ from: range.from, to: range.to })
                          setSelectedPreset("custom")
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
                {projectsData.map((project) => (
                  <SelectItem key={project.name} value={project.name}>
                    {project.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select value={selectedTag} onValueChange={setSelectedTag}>
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="Tag: All" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Tag: All</SelectItem>
                {tags.map((tag) => (
                  <SelectItem key={tag} value={tag}>
                    {tag}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Button variant="outline" onClick={() => { setSelectedProject("all"); setSelectedTag("all") }}>
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
                      {totalBillableHours.toFixed(2)} h - 100%
                    </p>
                  </div>
                </div>

                {/* Legend */}
                <div className="space-y-2">
                  {pieChartData.map((entry, index) => (
                    <div key={index} className="flex items-center gap-3">
                      <div
                        className="w-4 h-4 rounded"
                        style={{ backgroundColor: projectsData[index].color }}
                      />
                      <span className="text-sm flex-1">{entry.name}</span>
                      <span className="text-sm font-medium">{entry.percentage}%</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Right: Pie Chart */}
              <div className="flex items-center justify-center">
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
                      {pieChartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={projectsData[index].color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
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
                  {filteredProjects.map((project, index) => (
                    <TableRow key={index}>
                      <TableCell>
                        <div className="flex items-center gap-3">
                          <div
                            className="w-8 h-8 rounded flex items-center justify-center text-white text-sm font-medium"
                            style={{ backgroundColor: project.color }}
                          >
                            {project.name.charAt(0)}
                          </div>
                          <span className="font-medium">{project.name}</span>
                        </div>
                      </TableCell>
                      <TableCell className="text-right text-primary font-medium">
                        {project.hours.toFixed(2)}
                      </TableCell>
                      <TableCell className="text-right text-primary font-medium">
                        {project.billableHours.toFixed(2)}
                      </TableCell>
                    </TableRow>
                  ))}
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
