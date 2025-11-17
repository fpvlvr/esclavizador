"use client"

import { useState } from "react"
import { Clock } from 'lucide-react'
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { useRouter } from 'next/navigation'

export default function LoginPage() {
  const router = useRouter()
  const [formData, setFormData] = useState({
    email: "",
    password: "",
  })

  const [createAccountOpen, setCreateAccountOpen] = useState(false)
  const [createAccountData, setCreateAccountData] = useState({
    name: "",
    email: "",
    password: "",
    organization: "",
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    console.log("Login attempt:", formData)
    router.push("/")
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData((prev) => ({
      ...prev,
      [e.target.name]: e.target.value,
    }))
  }

  const handleCreateAccountChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setCreateAccountData((prev) => ({
      ...prev,
      [e.target.name]: e.target.value,
    }))
  }

  const handleCreateAccountSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    console.log("Create account:", createAccountData)
    setCreateAccountOpen(false)
    router.push("/")
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1 flex flex-col items-center">
          <div className="flex items-center gap-2 mb-2">
            <Clock className="h-8 w-8 text-primary" />
            <span className="text-2xl font-semibold">TimeTrack</span>
          </div>
          <CardTitle className="text-2xl">Welcome back</CardTitle>
          <CardDescription>Enter your credentials to access your account</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                name="email"
                type="email"
                placeholder="john@example.com"
                value={formData.email}
                onChange={handleChange}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                name="password"
                type="password"
                placeholder="••••••••"
                value={formData.password}
                onChange={handleChange}
                required
              />
            </div>
            <Button type="submit" className="w-full">
              Sign in
            </Button>
            <div className="text-center text-sm text-muted-foreground">
              New here?{" "}
              <Dialog open={createAccountOpen} onOpenChange={setCreateAccountOpen}>
                <DialogTrigger asChild>
                  <Button variant="link" className="p-0 h-auto font-normal">
                    Create account
                  </Button>
                </DialogTrigger>
                <DialogContent className="sm:max-w-[425px]">
                  <DialogHeader>
                    <DialogTitle>Create account</DialogTitle>
                    <DialogDescription>
                      Enter your details to create a new account
                    </DialogDescription>
                  </DialogHeader>
                  <form onSubmit={handleCreateAccountSubmit} className="space-y-4 mt-4">
                    <div className="space-y-2">
                      <Label htmlFor="create-name">Name</Label>
                      <Input
                        id="create-name"
                        name="name"
                        type="text"
                        placeholder="John Doe"
                        value={createAccountData.name}
                        onChange={handleCreateAccountChange}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="create-email">Email</Label>
                      <Input
                        id="create-email"
                        name="email"
                        type="email"
                        placeholder="john@example.com"
                        value={createAccountData.email}
                        onChange={handleCreateAccountChange}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="create-password">Password</Label>
                      <Input
                        id="create-password"
                        name="password"
                        type="password"
                        placeholder="••••••••"
                        value={createAccountData.password}
                        onChange={handleCreateAccountChange}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="create-organization">Organization Name</Label>
                      <Input
                        id="create-organization"
                        name="organization"
                        type="text"
                        placeholder="Your organization"
                        value={createAccountData.organization}
                        onChange={handleCreateAccountChange}
                        required
                      />
                    </div>
                    <Button type="submit" className="w-full">
                      Create account
                    </Button>
                  </form>
                </DialogContent>
              </Dialog>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
