import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '@/hooks'
import { ROUTE_PATHS, APP_NAME } from '@/constants'
import { Button } from '@/components/ui'
import { Eye, EyeOff, Lock, Mail } from 'lucide-react'
import { motion } from 'framer-motion'

export function Register() {
  const navigate = useNavigate()
  const { register } = useAuth()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [validationError, setValidationError] = useState('')
  const [serverError, setServerError] = useState('')

  const togglePasswordVisibility = () => {
    setShowPassword((prev) => !prev)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setValidationError('')
    setServerError('')

    // Client-side validations
    if (!email.trim() || !password || !confirmPassword) {
      setValidationError('All fields are required.')
      return
    }

    if (password.length < 8) {
      setValidationError('Password must be at least 8 characters long.')
      return
    }

    if (password !== confirmPassword) {
      setValidationError('Passwords do not match.')
      return
    }

    setLoading(true)
    try {
      await register(email.trim(), password)
      // Registration successful! Redirect to login page and pass success details
      navigate(ROUTE_PATHS.LOGIN, {
        state: {
          registeredEmail: email.trim(),
          successMessage: 'Account created successfully! Please sign in using your credentials.',
        },
      })
    } catch (err) {
      console.error('Registration error in form:', err)
      // Backend checks for duplicate emails and returns "User already exists."
      setServerError(err.message || 'Registration failed. Please try again.')
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
          Create Account
        </h3>
        <p className="text-xs font-bold text-text-muted">
          Register with your email to start monitoring your budgets, goals, and assets.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        {/* Email Field */}
        <div className="flex flex-col gap-1.5 relative">
          <label
            htmlFor="register-email"
            className="text-[10px] font-black text-text-muted uppercase tracking-wider"
          >
            Email Address
          </label>
          <div className="relative flex items-center">
            <span className="absolute left-3 text-text-muted">
              <Mail size={14} />
            </span>
            <input
              id="register-email"
              type="email"
              name="email"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value)
                setValidationError('')
                setServerError('')
              }}
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
            htmlFor="register-password"
            className="text-[10px] font-black text-text-muted uppercase tracking-wider"
          >
            Password
          </label>
          <div className="relative flex items-center">
            <span className="absolute left-3 text-text-muted">
              <Lock size={14} />
            </span>
            <input
              id="register-password"
              type={showPassword ? 'text' : 'password'}
              name="password"
              value={password}
              onChange={(e) => {
                setPassword(e.target.value)
                setValidationError('')
                setServerError('')
              }}
              required
              placeholder="••••••••"
              autoComplete="new-password"
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

        {/* Confirm Password Field */}
        <div className="flex flex-col gap-1.5 relative">
          <label
            htmlFor="register-confirm-password"
            className="text-[10px] font-black text-text-muted uppercase tracking-wider"
          >
            Confirm Password
          </label>
          <div className="relative flex items-center">
            <span className="absolute left-3 text-text-muted">
              <Lock size={14} />
            </span>
            <input
              id="register-confirm-password"
              type={showPassword ? 'text' : 'password'}
              name="confirmPassword"
              value={confirmPassword}
              onChange={(e) => {
                setConfirmPassword(e.target.value)
                setValidationError('')
                setServerError('')
              }}
              required
              placeholder="••••••••"
              autoComplete="new-password"
              disabled={loading}
              className="w-full pl-9 pr-10 py-2.5 text-xs font-bold rounded-xl border border-border bg-card text-text-primary focus:outline-none focus:border-primary disabled:opacity-50"
            />
          </div>
        </div>

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
          {loading ? 'Registering...' : 'Register'}
        </Button>
      </form>

      {/* Footer Link */}
      <div className="text-center text-xs font-bold text-text-muted mt-2 border-t border-border/40 pt-4 flex items-center justify-center gap-1.5">
        <span>Already have an account?</span>
        <Link
          to={ROUTE_PATHS.LOGIN}
          className="text-primary hover:underline font-extrabold focus:outline-none focus:ring-1 focus:ring-primary rounded px-1"
        >
          Sign In
        </Link>
      </div>
    </motion.div>
  )
}

export default Register
