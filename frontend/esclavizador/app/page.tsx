import { ProtectedRoute } from "@/components/protected-route"
import { Sidebar } from "@/components/sidebar"
import { TimeTracker } from "@/components/time-tracker"
import { DailyTimeline } from "@/components/daily-timeline"

export default function Home() {
  return (
    <ProtectedRoute>
      <div className="flex min-h-screen bg-background">
        <Sidebar />

        <main className="flex-1 lg:ml-64">
          <div className="container mx-auto px-4 lg:px-8 pt-6 pb-4 lg:pb-8 space-y-6">
            {/* Timer Section */}
            <TimeTracker />

            {/* Daily Timeline */}
            <DailyTimeline />
          </div>
        </main>
      </div>
    </ProtectedRoute>
  )
}
