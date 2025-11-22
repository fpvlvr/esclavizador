"use client"

import { useState } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { Clock, Github } from 'lucide-react'
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { PasswordInput } from "@/components/ui/password-input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { useAuth } from "@/hooks/use-auth"
import { toast } from "sonner"

// Login form validation schema
const loginSchema = z.object({
  email: z.string().email("Invalid email address"),
  password: z.string().min(1, "Password is required"),
})

type LoginFormData = z.infer<typeof loginSchema>

// Register form validation schema
const registerSchema = z.object({
  email: z.string().email("Invalid email address"),
  password: z
    .string()
    .min(8, "Password must be at least 8 characters")
    .regex(/[a-z]/, "Password must contain at least one lowercase letter")
    .regex(/[A-Z]/, "Password must contain at least one uppercase letter")
    .regex(/[0-9]/, "Password must contain at least one digit")
    .regex(/[^a-zA-Z0-9]/, "Password must contain at least one special character"),
  organization: z.string().min(2, "Organization name must be at least 2 characters"),
})

type RegisterFormData = z.infer<typeof registerSchema>

export default function LoginPage() {
  const { login, register } = useAuth()
  const [createAccountOpen, setCreateAccountOpen] = useState(false)
  const [forgotPasswordOpen, setForgotPasswordOpen] = useState(false)
  const [isLoggingIn, setIsLoggingIn] = useState(false)
  const [isRegistering, setIsRegistering] = useState(false)

  // Login form
  const loginForm = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: "",
      password: "",
    },
  })

  // Register form
  const registerForm = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      email: "",
      password: "",
      organization: "",
    },
  })

  const handleLoginSubmit = async (data: LoginFormData) => {
    setIsLoggingIn(true)
    try {
      await login(data.email, data.password)
      toast.success("Logged in successfully")
    } catch (error) {
      const message = error instanceof Error ? error.message : "Login failed"
      toast.error(message)
    } finally {
      setIsLoggingIn(false)
    }
  }

  const handleRegisterSubmit = async (data: RegisterFormData) => {
    setIsRegistering(true)
    try {
      await register(data.email, data.password, data.organization)
      toast.success("Account created successfully")
      setCreateAccountOpen(false)
    } catch (error) {
      const message = error instanceof Error ? error.message : "Registration failed"
      toast.error(message)
    } finally {
      setIsRegistering(false)
    }
  }

  const handleDemoLogin = async () => {
    setIsLoggingIn(true)
    try {
      await login("mike.oxlong@sample.org", "SecurePass123!")
      toast.success("Logged in with demo account")
    } catch (error) {
      const message = error instanceof Error ? error.message : "Demo login failed"
      toast.error(message)
    } finally {
      setIsLoggingIn(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4 relative">
      {/* GitHub link */}
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <a
              href="https://github.com/fpvlvr/esclavizador"
              target="_blank"
              rel="noopener noreferrer"
              aria-label="View source code on GitHub"
              className="absolute top-4 right-4 p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
            >
              <Github className="h-6 w-6" />
            </a>
          </TooltipTrigger>
          <TooltipContent>
            <p>View on GitHub</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>

      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1 flex flex-col items-center">
          <div className="flex items-center gap-2 mb-2">
            <Clock className="h-8 w-8 text-primary" />
            <span className="text-2xl font-semibold">Esclavizador</span>
          </div>
          <CardTitle className="text-2xl">Welcome back</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={loginForm.handleSubmit(handleLoginSubmit)} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="john@example.com"
                {...loginForm.register("email")}
              />
              {loginForm.formState.errors.email && (
                <p className="text-sm text-destructive">
                  {loginForm.formState.errors.email.message}
                </p>
              )}
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="password">Password</Label>
                <Dialog open={forgotPasswordOpen} onOpenChange={setForgotPasswordOpen}>
                  <DialogTrigger asChild>
                    <Button variant="link" className="p-0 h-auto text-xs font-normal">
                      Forgot password?
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="sm:max-w-lg">
                    <DialogHeader>
                      <DialogTitle>Oops...</DialogTitle>
                    </DialogHeader>
                    <div className="py-4 space-y-3">
                      <p className="text-foreground font-medium">
                        Too bad. Password reset is not really implemented yet.
                      </p>
                      <p className="text-sm text-muted-foreground">
                        If you're a Simple Worker, ask your Boss for a new one. If you're a Big Boss… well, maybe don't rely on your memory next time! 😎
                      </p>
                      <p className="text-sm text-muted-foreground">
                        Want me to suggest a few{" "}
                        <a
                          href="https://letmegooglethat.com/?q=best+password+manager+2026"
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-primary hover:underline"
                        >
                          good password managers
                        </a>
                        ?
                      </p>
                      <p className="text-sm text-muted-foreground pt-2">
                        JK, please drop me a line at{" "}
                        <a
                          href="mailto:fpv-lover@proton.me"
                          className="text-primary hover:underline"
                        >
                          fpv-lover@proton.me
                        </a>
                      </p>
                    </div>
                  </DialogContent>
                </Dialog>
              </div>
              <PasswordInput
                id="password"
                placeholder="••••••••"
                {...loginForm.register("password")}
              />
              {loginForm.formState.errors.password && (
                <p className="text-sm text-destructive">
                  {loginForm.formState.errors.password.message}
                </p>
              )}
            </div>
            <Button type="submit" className="w-full" disabled={isLoggingIn}>
              {isLoggingIn ? "Signing in..." : "Sign in"}
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
                      Enter your details to create a new account and organization
                    </DialogDescription>
                  </DialogHeader>
                  <form onSubmit={registerForm.handleSubmit(handleRegisterSubmit)} className="space-y-4 mt-4">
                    <div className="space-y-2">
                      <Label htmlFor="register-email">Email</Label>
                      <Input
                        id="register-email"
                        type="email"
                        placeholder="john@example.com"
                        {...registerForm.register("email")}
                      />
                      {registerForm.formState.errors.email && (
                        <p className="text-sm text-destructive">
                          {registerForm.formState.errors.email.message}
                        </p>
                      )}
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="register-password">Password</Label>
                      <PasswordInput
                        id="register-password"
                        placeholder="••••••••"
                        {...registerForm.register("password")}
                      />
                      {registerForm.formState.errors.password && (
                        <p className="text-sm text-destructive">
                          {registerForm.formState.errors.password.message}
                        </p>
                      )}
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="register-organization">Organization Name</Label>
                      <Input
                        id="register-organization"
                        type="text"
                        placeholder="Your organization"
                        {...registerForm.register("organization")}
                      />
                      {registerForm.formState.errors.organization && (
                        <p className="text-sm text-destructive">
                          {registerForm.formState.errors.organization.message}
                        </p>
                      )}
                    </div>
                    <Button type="submit" className="w-full" disabled={isRegistering}>
                      {isRegistering ? "Creating account..." : "Create account"}
                    </Button>
                  </form>
                </DialogContent>
              </Dialog>
            </div>
            <div className="relative my-4">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-background px-2 text-muted-foreground">or</span>
              </div>
            </div>
            <div className="text-center">
              <Button
                type="button"
                variant="link"
                className="text-sm font-normal"
                onClick={handleDemoLogin}
                disabled={isLoggingIn}
              >
                Explore with sample organization
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
