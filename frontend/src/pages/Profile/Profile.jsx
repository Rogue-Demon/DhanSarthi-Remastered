import React, { useState, useEffect } from 'react'
import { useAuth, useProfile } from '@/hooks'
import { Button, Badge } from '@/components/ui'
import Avatar from '@/components/ui/Avatar'
import Alert from '@/components/feedback/Alert'
import Toast from '@/components/feedback/Toast'
import { apiClient, ENDPOINTS } from '@/services/api'
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion'
import {
  User,
  Mail,
  Phone,
  Briefcase,
  Calendar,
  Shield,
  ArrowRight,
  Settings,
  Lock,
  Edit2,
  X,
  Check,
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'

export default function Profile() {
  const navigate = useNavigate()
  const shouldReduceMotion = useReducedMotion()
  const { user, updateLocalProfile, loading: authLoading } = useAuth()
  const { profile: activePersona } = useProfile()

  const [isEditing, setIsEditing] = useState(false)
  const [saving, setSaving] = useState(false)
  const [successMsg, setSuccessMsg] = useState('')
  const [errorMsg, setErrorMsg] = useState('')

  const [formData, setFormData] = useState({
    displayName: '',
    phone: '',
    occupation: '',
  })

  const [validationErrors, setValidationErrors] = useState({
    displayName: '',
    phone: '',
    occupation: '',
  })

  // Sync profile data when user state loaded or edit mode toggled
  useEffect(() => {
    if (user?.profile) {
      /* eslint-disable-next-line react-hooks/set-state-in-effect */
      setFormData({
        displayName: user.profile.display_name || '',
        phone: user.profile.phone || '',
        occupation: user.profile.occupation || '',
      })
      setValidationErrors({
        displayName: '',
        phone: '',
        occupation: '',
      })
    }
  }, [user, isEditing])

  const profile = user?.profile || {}
  const email = user?.email || ''
  const displayTitleName = profile.display_name || email.split('@')[0] || 'User'
  const displayPersona = activePersona || profile.persona || 'PROFESSIONAL'

  // Get initials for Avatar dynamically
  const getInitials = (nameStr, emailStr) => {
    if (nameStr && nameStr.trim()) {
      const parts = nameStr.trim().split(/\s+/)
      if (parts.length >= 2) {
        return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
      }
      return parts[0][0].toUpperCase()
    }
    if (emailStr && emailStr.trim()) {
      return emailStr.trim()[0].toUpperCase()
    }
    return '?'
  }

  const avatarInitials = getInitials(profile.display_name, email)

  // Validate form inputs
  const validateForm = () => {
    const errors = { displayName: '', phone: '', occupation: '' }
    let isValid = true

    // Full name validations
    if (!formData.displayName || !formData.displayName.trim()) {
      errors.displayName = 'Full Name is required.'
      isValid = false
    } else if (formData.displayName.length > 100) {
      errors.displayName = 'Name must be less than 100 characters.'
      isValid = false
    }

    // Phone validations (if provided)
    if (formData.phone && formData.phone.trim()) {
      const phoneRegex = /^[+]?[0-9\s-]{7,20}$/
      if (!phoneRegex.test(formData.phone.trim())) {
        errors.phone = 'Please enter a valid phone number (7-20 digits).'
        isValid = false
      }
    }

    // Occupation validations (if provided)
    if (formData.occupation && formData.occupation.length > 100) {
      errors.occupation = 'Occupation must be less than 100 characters.'
      isValid = false
    }

    setValidationErrors(errors)
    return isValid
  }

  const handleInputChange = (field, val) => {
    setFormData((prev) => ({ ...prev, [field]: val }))
    if (validationErrors[field]) {
      setValidationErrors((prev) => ({ ...prev, [field]: '' }))
    }
  }

  const handleCancel = () => {
    setIsEditing(false)
    setErrorMsg('')
  }

  const handleSave = async (e) => {
    e.preventDefault()
    if (saving) return

    setErrorMsg('')
    setSuccessMsg('')

    if (!validateForm()) {
      return
    }

    setSaving(true)

    try {
      const payload = {
        display_name: formData.displayName.trim(),
        phone: formData.phone.trim() || null,
        occupation: formData.occupation.trim() || null,
      }

      const response = await apiClient.patch(ENDPOINTS.profile.update, payload)
      updateLocalProfile(response)
      setSuccessMsg('Profile updated successfully.')
      setIsEditing(false)
    } catch (err) {
      console.error('Failed to save profile:', err)
      setErrorMsg(err.message || 'Unable to update your profile. Please try again.')
    } finally {
      setSaving(false)
    }
  }

  // Render Loading / Skeleton State
  if (authLoading || !user) {
    return (
      <div className="p-6 max-w-4xl mx-auto flex flex-col gap-8 text-left select-none animate-pulse">
        <div className="flex flex-col gap-2">
          <div className="h-8 w-48 bg-muted rounded-xl" />
          <div className="h-4 w-80 bg-muted rounded-lg mt-1" />
        </div>

        {/* Summary Card Skeleton */}
        <div className="clay-surface bg-card p-6 border border-white/60 dark:border-white/5 rounded-3xl flex items-center gap-6 shadow-card">
          <div className="h-16 w-16 rounded-2xl bg-muted" />
          <div className="flex flex-col gap-2 flex-grow">
            <div className="h-5 w-40 bg-muted rounded-md" />
            <div className="h-3 w-56 bg-muted rounded-md" />
          </div>
        </div>

        {/* Form Card Skeleton */}
        <div className="clay-surface bg-card p-8 border border-white/60 dark:border-white/5 rounded-3xl flex flex-col gap-6 shadow-card">
          <div className="h-6 w-32 bg-muted rounded-md mb-2" />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="flex flex-col gap-2">
                <div className="h-3.5 w-20 bg-muted rounded" />
                <div className="h-10 w-full bg-muted rounded-xl" />
              </div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  const formattedJoinedDate = user.created_at
    ? new Date(user.created_at).toLocaleDateString(undefined, {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      })
    : 'Not Available'

  return (
    <motion.div
      initial={{ opacity: 0, y: shouldReduceMotion ? 0 : 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: 'easeOut' }}
      className="p-6 max-w-4xl mx-auto flex flex-col gap-8 text-left select-none relative"
    >
      {/* Header title */}
      <div className="flex flex-col gap-1.5">
        <h1 className="text-3xl font-black text-text-primary tracking-tight">Profile</h1>
        <p className="text-sm font-semibold text-text-muted">
          Manage your personal information and account details.
        </p>
      </div>

      {/* Success/Error Toasts */}
      <AnimatePresence>
        {successMsg && (
          <Toast message={successMsg} type="success" onClose={() => setSuccessMsg('')} />
        )}
      </AnimatePresence>

      {errorMsg && (
        <Alert
          variant="danger"
          description={errorMsg}
          onClose={() => setErrorMsg('')}
          className="mb-2"
        />
      )}

      {/* Profile Header Summary Card */}
      <div className="clay-surface bg-card p-6 border border-white/60 dark:border-white/5 rounded-3xl flex flex-col sm:flex-row items-center gap-6 shadow-card">
        <div className="h-16 w-16 rounded-2xl bg-gradient-primary flex items-center justify-center text-white text-xl font-black shadow-floating shrink-0 select-none">
          {avatarInitials}
        </div>
        <div className="flex flex-col gap-1 text-center sm:text-left flex-grow">
          <div className="flex flex-col sm:flex-row sm:items-center gap-2">
            <h2 className="text-xl font-black text-text-primary leading-tight">
              {displayTitleName}
            </h2>
            <Badge
              variant="primary"
              className="text-[10px] font-bold py-0.5 px-2 bg-primary/10 text-primary border-primary/20 rounded-md self-center sm:self-start uppercase"
            >
              {displayPersona}
            </Badge>
          </div>
          <span className="text-xs font-semibold text-text-muted select-text">{email}</span>
        </div>
        {!isEditing && (
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setIsEditing(true)}
            iconLeft={<Edit2 className="w-4 h-4" />}
            className="rounded-xl shadow-xs self-stretch sm:self-center"
          >
            Edit Profile
          </Button>
        )}
      </div>

      {/* Main Info Columns */}
      <div className="grid grid-cols-1 gap-8">
        {/* Personal Information Form Card */}
        <form
          onSubmit={handleSave}
          className="clay-surface bg-card p-8 border border-white/60 dark:border-white/5 rounded-3xl shadow-card flex flex-col gap-6"
        >
          <div className="flex items-center justify-between border-b border-border/60 pb-4">
            <h3 className="text-base font-black text-text-primary uppercase tracking-wider">
              Personal Information
            </h3>
            {isEditing && (
              <Badge
                variant="warning"
                className="text-[9px] font-bold uppercase rounded py-0.5 px-1.5"
              >
                Editing Mode
              </Badge>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-left">
            {/* Full Name */}
            <div className="flex flex-col gap-2">
              <label
                htmlFor="displayName"
                className="text-[10px] font-black text-text-muted uppercase tracking-wider"
              >
                Full Name <span className="text-destructive">*</span>
              </label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center text-text-muted">
                  <User className="h-4 w-4" />
                </span>
                <input
                  id="displayName"
                  type="text"
                  required
                  disabled={!isEditing || saving}
                  value={formData.displayName}
                  onChange={(e) => handleInputChange('displayName', e.target.value)}
                  placeholder="Enter your full name"
                  className={`w-full pl-10 pr-3.5 py-3 text-xs font-bold rounded-xl border bg-card text-text-primary focus:outline-none focus:ring-2 focus:ring-primary/20 ${
                    validationErrors.displayName
                      ? 'border-destructive focus:ring-destructive/20'
                      : 'border-border focus:border-primary'
                  } ${!isEditing ? 'cursor-not-allowed opacity-80 bg-muted/30' : ''}`}
                />
              </div>
              {validationErrors.displayName && (
                <span className="text-[10px] font-semibold text-destructive mt-0.5">
                  {validationErrors.displayName}
                </span>
              )}
            </div>

            {/* Email (Read-only) */}
            <div className="flex flex-col gap-2">
              <label
                htmlFor="emailAddress"
                className="text-[10px] font-black text-text-muted uppercase tracking-wider"
              >
                Email Address
              </label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center text-text-muted">
                  <Mail className="h-4 w-4" />
                </span>
                <input
                  id="emailAddress"
                  type="email"
                  readOnly
                  disabled
                  value={email}
                  className="w-full pl-10 pr-10 py-3 text-xs font-bold rounded-xl border border-border bg-muted/40 text-text-muted cursor-not-allowed outline-none select-text"
                />
                <span
                  className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-text-muted"
                  title="Email is read-only"
                >
                  <Lock className="h-4 w-4" />
                </span>
              </div>
            </div>

            {/* Phone */}
            <div className="flex flex-col gap-2">
              <label
                htmlFor="phoneNumber"
                className="text-[10px] font-black text-text-muted uppercase tracking-wider"
              >
                Phone Number
              </label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center text-text-muted">
                  <Phone className="h-4 w-4" />
                </span>
                <input
                  id="phoneNumber"
                  type="tel"
                  disabled={!isEditing || saving}
                  value={formData.phone}
                  onChange={(e) => handleInputChange('phone', e.target.value)}
                  placeholder={!isEditing ? 'Not added' : 'e.g. +91 9876543210'}
                  className={`w-full pl-10 pr-3.5 py-3 text-xs font-bold rounded-xl border bg-card text-text-primary focus:outline-none focus:ring-2 focus:ring-primary/20 ${
                    validationErrors.phone
                      ? 'border-destructive focus:ring-destructive/20'
                      : 'border-border focus:border-primary'
                  } ${!isEditing ? 'cursor-not-allowed opacity-80 bg-muted/30' : ''}`}
                />
              </div>
              {validationErrors.phone && (
                <span className="text-[10px] font-semibold text-destructive mt-0.5">
                  {validationErrors.phone}
                </span>
              )}
            </div>

            {/* Occupation */}
            <div className="flex flex-col gap-2">
              <label
                htmlFor="occupation"
                className="text-[10px] font-black text-text-muted uppercase tracking-wider"
              >
                Occupation
              </label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center text-text-muted">
                  <Briefcase className="h-4 w-4" />
                </span>
                <input
                  id="occupation"
                  type="text"
                  disabled={!isEditing || saving}
                  value={formData.occupation}
                  onChange={(e) => handleInputChange('occupation', e.target.value)}
                  placeholder={!isEditing ? 'Not added' : 'e.g. Software Engineer'}
                  className={`w-full pl-10 pr-3.5 py-3 text-xs font-bold rounded-xl border bg-card text-text-primary focus:outline-none focus:ring-2 focus:ring-primary/20 ${
                    validationErrors.occupation
                      ? 'border-destructive focus:ring-destructive/20'
                      : 'border-border focus:border-primary'
                  } ${!isEditing ? 'cursor-not-allowed opacity-80 bg-muted/30' : ''}`}
                />
              </div>
              {validationErrors.occupation && (
                <span className="text-[10px] font-semibold text-destructive mt-0.5">
                  {validationErrors.occupation}
                </span>
              )}
            </div>
          </div>

          {/* View Mode Hints or Edit Mode Actions */}
          {isEditing ? (
            <div className="flex justify-end gap-3 pt-4 border-t border-border/60">
              <Button
                variant="ghost"
                size="sm"
                onClick={handleCancel}
                disabled={saving}
                iconLeft={<X className="w-4 h-4" />}
                className="rounded-xl"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="gradient"
                size="sm"
                loading={saving}
                iconLeft={<Check className="w-4 h-4" />}
                className="rounded-xl shadow-button"
              >
                {saving ? 'Saving...' : 'Save Changes'}
              </Button>
            </div>
          ) : (
            <p className="text-[10px] font-medium text-text-muted text-center sm:text-right border-t border-border/60 pt-4">
              Fields marked with an asterisk (*) are mandatory. Click Edit Profile to make changes.
            </p>
          )}
        </form>

        {/* Account Information Card (Read-only) */}
        <div className="clay-surface bg-card p-8 border border-white/60 dark:border-white/5 rounded-3xl shadow-card flex flex-col gap-6">
          <div className="border-b border-border/60 pb-4">
            <h3 className="text-base font-black text-text-primary uppercase tracking-wider">
              Account Metadata
            </h3>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 text-left">
            {/* Account ID */}
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-xl bg-primary/5 text-primary mt-0.5">
                <Shield className="h-4.5 w-4.5" />
              </div>
              <div className="flex flex-col">
                <span className="text-[9px] font-black text-text-muted uppercase tracking-wider">
                  User Account ID
                </span>
                <span className="text-xs font-bold text-text-primary mt-0.5 select-text">
                  USR-{user.id || 'N/A'}
                </span>
              </div>
            </div>

            {/* Account Status */}
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-xl bg-success/5 text-success mt-0.5">
                <Check className="h-4.5 w-4.5" />
              </div>
              <div className="flex flex-col">
                <span className="text-[9px] font-black text-text-muted uppercase tracking-wider">
                  Account Status
                </span>
                <div className="mt-0.5">
                  <Badge
                    variant="success"
                    className="text-[9px] font-bold uppercase rounded py-0.5 px-2"
                  >
                    Active
                  </Badge>
                </div>
              </div>
            </div>

            {/* Account Created Date */}
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-xl bg-primary/5 text-primary mt-0.5">
                <Calendar className="h-4.5 w-4.5" />
              </div>
              <div className="flex flex-col">
                <span className="text-[9px] font-black text-text-muted uppercase tracking-wider">
                  Joined DhanSarthi
                </span>
                <span className="text-xs font-bold text-text-primary mt-0.5">
                  {formattedJoinedDate}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Links Card */}
        <div className="clay-surface bg-card p-6 border border-white/60 dark:border-white/5 rounded-3xl shadow-card flex flex-col sm:flex-row justify-between gap-4">
          <button
            onClick={() => navigate('/finance')}
            className="flex items-center justify-between p-4 rounded-2xl border border-border bg-muted/30 hover:bg-primary/5 hover:border-primary/20 text-left transition-all duration-200 flex-1 group cursor-pointer"
          >
            <div className="flex flex-col gap-0.5">
              <span className="text-xs font-black text-text-primary uppercase tracking-wider">
                Financial Overview
              </span>
              <span className="text-[10px] text-text-muted font-bold">
                Monitor your active capital, income & budgets.
              </span>
            </div>
            <ArrowRight className="h-5 w-5 text-text-muted group-hover:text-primary transition-colors duration-200" />
          </button>

          <button
            onClick={() => navigate('/settings')}
            className="flex items-center justify-between p-4 rounded-2xl border border-border bg-muted/30 hover:bg-primary/5 hover:border-primary/20 text-left transition-all duration-200 flex-1 group cursor-pointer"
          >
            <div className="flex flex-col gap-0.5">
              <span className="text-xs font-black text-text-primary uppercase tracking-wider">
                Security & settings
              </span>
              <span className="text-[10px] text-text-muted font-bold">
                Manage your security credentials and system configurations.
              </span>
            </div>
            <Settings className="h-5 w-5 text-text-muted group-hover:text-primary transition-colors duration-200" />
          </button>
        </div>
      </div>
    </motion.div>
  )
}
