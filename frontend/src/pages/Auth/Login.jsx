import React, { useState, useEffect } from 'react'
import { useNavigate, Link, useLocation } from 'react-router-dom'
import { useAuth } from '@/hooks'
import { ROUTE_PATHS, APP_NAME } from '@/constants'
import { Button } from '@/components/ui'
import { Eye, EyeOff, Lock, Mail } from 'lucide-react'
import { motion } from 'framer-motion'

export function Login() {
  const navigate = useNavigate()
  const location = useLocation()
  const { login } = useAuth()

  const successMessage = location.state?.successMessage || ''
  const initialEmail = location.state?.registeredEmail || ''

  const [email, setEmail] = useState(initialEmail)
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [validationError, setValidationError] = useState('')
  const [serverError, setServerError] = useState('')

  // Clear state when user starts changing inputs
  const handleInputChange = (setter, value) => {
    setter(value)
    setValidationError('')
    setServerError('')
    if (location.state) {
      // Clear location state so the message disappears if they edit the inputs
      window.history.replaceState({}, document.title)
    }
  }

  const togglePasswordVisibility = () => {
    setShowPassword((prev) => !prev)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setValidationError('')
    setServerError('')

    // Basic client validation
    if (!email.trim() || !password.trim()) {
      setValidationError('Please enter both email and password.')
      return
    }

    setLoading(true)
    try {
      await login(email.trim(), password)
      // Success: redirect to dashboard
      navigate(ROUTE_PATHS.DASHBOARD)
    } catch (err) {
      console.error('Login error in form:', err)
      setServerError(err.message || 'Invalid email or password.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="flex flex-col gap-6 text-left"
    >
      {/* Brand Header */}
      <div className="flex flex-col gap-2 text-center items-center">
        <h2 className="text-3xl font-black text-primary tracking-wider leading-none">{APP_NAME}</h2>
        <p className="text-xs font-bold text-text-muted">
          Your Smart Financial Journey Starts Here
        </p>
      </div>

      <div className="flex flex-col gap-1.5">
        <h3 className="text-lg font-black text-text-primary uppercase tracking-wide leading-none">
          Sign In
        </h3>
        <p className="text-xs font-bold text-text-muted">
          Enter your registered email and password to access your dashboard.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        {/* Email Field */}
        <div className="flex flex-col gap-1.5 relative">
          <label
            htmlFor="login-email"
            className="text-[10px] font-black text-text-muted uppercase tracking-wider"
          >
            Email Address
          </label>
          <div className="relative flex items-center">
            <span className="absolute left-3 text-text-muted">
              <Mail size={14} />
            </span>
            <input
              id="login-email"
              type="email"
              name="email"
              value={email}
              onChange={(e) => handleInputChange(setEmail, e.target.value)}
              required
              placeholder="name@example.com"
              autoComplete="email"
              disabled={loading}
              className="w-full pl-9 pr-3.5 py-2.5 text-xs font-bold rounded-xl border border-border bg-card text-text-primary focus:outline-none focus:border-primary disabled:opacity-50"
            />
          </div>
        </div>

        {/* Password Field */}
        <div className="flex flex-col gap-1.5 relative">
          <label
            htmlFor="login-password"
            className="text-[10px] font-black text-text-muted uppercase tracking-wider"
          >
            Password
          </label>
          <div className="relative flex items-center">
            <span className="absolute left-3 text-text-muted">
              <Lock size={14} />
            </span>
            <input
              id="login-password"
              type={showPassword ? 'text' : 'password'}
              name="password"
              value={password}
              onChange={(e) => handleInputChange(setPassword, e.target.value)}
              required
              placeholder="••••••••"
              autoComplete="current-password"
              disabled={loading}
              className="w-full pl-9 pr-10 py-2.5 text-xs font-bold rounded-xl border border-border bg-card text-text-primary focus:outline-none focus:border-primary disabled:opacity-50"
            />
            <button
              type="button"
              onClick={togglePasswordVisibility}
              tabIndex="-1"
              aria-label={showPassword ? 'Hide password' : 'Show password'}
              className="absolute right-3 text-text-muted hover:text-text-primary focus:outline-none"
            >
              {showPassword ? <EyeOff size={14} /> : <Eye size={14} />}
            </button>
          </div>
        </div>

        {/* Success Message from Redirect */}
        {successMessage && !serverError && !validationError && (
          <div className="text-[11px] font-semibold text-success bg-success/10 border border-success/20 px-3 py-2 rounded-xl">
            {successMessage}
          </div>
        )}

        {/* Local Validation Error */}
        {validationError && (
          <div
            role="alert"
            className="text-[11px] font-semibold text-danger bg-danger/10 border border-danger/20 px-3 py-2 rounded-xl"
          >
            {validationError}
          </div>
        )}

        {/* Server Auth Error */}
        {serverError && (
          <div
            role="alert"
            className="text-[11px] font-semibold text-danger bg-danger/10 border border-danger/20 px-3 py-2 rounded-xl"
          >
            {serverError}
          </div>
        )}

        {/* Submit button */}
        <Button
          type="submit"
          variant="primary"
          loading={loading}
          disabled={loading}
          fullWidth
          className="mt-2 font-bold py-2.5 rounded-xl uppercase tracking-wider text-xs shadow-floating"
        >
          {loading ? 'Signing in...' : 'Sign In'}
        </Button>
      </form>

      {/* Footer Link */}
      <div className="text-center text-xs font-bold text-text-muted mt-2 border-t border-border/40 pt-4 flex items-center justify-center gap-1.5">
        <span>Don't have an account?</span>
        <Link
          to={ROUTE_PATHS.ONBOARDING}
          className="text-primary hover:underline font-extrabold focus:outline-none focus:ring-1 focus:ring-primary rounded px-1"
        >
          Register Now
        </Link>
      </div>
    </motion.div>
  )
}

export default Login
