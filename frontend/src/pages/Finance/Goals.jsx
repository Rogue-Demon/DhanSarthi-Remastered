import React, { useState } from 'react'
import { useProfile, useGoals, useCreateGoal, useDeleteGoal, useUpdateGoal } from '@/hooks'
import { motion, useReducedMotion } from 'framer-motion'
import { DashboardGrid } from '@/components/dashboard'
import * as LucideIcons from 'lucide-react'
import { Badge, Button } from '@/components/ui'
import {
  Modal,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ConfirmationDialog,
} from '@/components/overlay'
import { Input, Select, FieldLabel } from '@/components/forms'

export function Goals() {
  const { profile } = useProfile()
  const shouldReduceMotion = useReducedMotion()

  // Queries & Mutations
  const { data: goalsData, isLoading } = useGoals()
  const createGoalMutation = useCreateGoal()
  const updateGoalMutation = useUpdateGoal()
  const deleteGoalMutation = useDeleteGoal()

  // Modal & Dialog state
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [deleteTargetId, setDeleteTargetId] = useState(null)
  const [editingItem, setEditingItem] = useState(null)

  // Form state
  const [formTitle, setFormTitle] = useState('')
  const [formTarget, setFormTarget] = useState('')
  const [formCurrent, setFormCurrent] = useState('0')
  const [formDate, setFormDate] = useState('')
  const [formPriority, setFormPriority] = useState('3')
  const [formStatus, setFormStatus] = useState('ACTIVE')
  const [formError, setFormError] = useState(null)

  const handleAddClick = () => {
    setEditingItem(null)
    setFormTitle('')
    setFormTarget('')
    setFormCurrent('0')
    setFormDate('')
    setFormPriority('3')
    setFormStatus('ACTIVE')
    setFormError(null)
    setIsModalOpen(true)
  }

  const handleEditClick = (item) => {
    setEditingItem(item)
    setFormTitle(item.title)
    setFormTarget(item.target_amount.toString())
    setFormCurrent(item.current_amount.toString())
    setFormDate(item.target_date || '')
    setFormPriority(item.priority.toString())
    setFormStatus(item.status)
    setFormError(null)
    setIsModalOpen(true)
  }

  const handleFormSubmit = async (e) => {
    e.preventDefault()
    setFormError(null)

    const targetVal = parseFloat(formTarget)
    const currentVal = parseFloat(formCurrent || '0')
    const priorityVal = parseInt(formPriority, 10)

    if (!formTitle.trim()) {
      setFormError('Goal title is required.')
      return
    }
    if (isNaN(targetVal) || targetVal <= 0) {
      setFormError('Target amount must be a positive number.')
      return
    }
    if (isNaN(currentVal) || currentVal < 0) {
      setFormError('Current saved amount cannot be negative.')
      return
    }
    if (currentVal > targetVal) {
      setFormError('Current saved amount cannot exceed the target.')
      return
    }

    const payload = {
      title: formTitle,
      target_amount: targetVal,
      current_amount: currentVal,
      target_date: formDate || null,
      priority: priorityVal,
      status: formStatus,
    }

    try {
      if (editingItem) {
        await updateGoalMutation.mutateAsync({
          id: editingItem.id,
          data: payload,
        })
      } else {
        await createGoalMutation.mutateAsync(payload)
      }
      setIsModalOpen(false)
    } catch (err) {
      setFormError(err.message || 'Failed to establish goal target.')
    }
  }

  const handleDeleteConfirm = async () => {
    if (!deleteTargetId) return
    try {
      await deleteGoalMutation.mutateAsync(deleteTargetId)
      setDeleteTargetId(null)
    } catch (err) {
      alert(err.message || 'Failed to remove goal.')
    }
  }

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 w-full animate-pulse">
        <div className="h-28 bg-muted/20 rounded-2xl border" />
        <div className="h-28 bg-muted/20 rounded-2xl border" />
        <div className="h-28 bg-muted/20 rounded-2xl border" />
      </div>
    )
  }

  const items = goalsData?.items || []

  // Goal Icon Mapper
  const getGoalIcon = (title) => {
    const t = title.toLowerCase()
    if (t.includes('car') || t.includes('vehicle')) return LucideIcons.Car
    if (t.includes('home') || t.includes('house') || t.includes('flat')) return LucideIcons.Home
    if (t.includes('education') || t.includes('college') || t.includes('university'))
      return LucideIcons.GraduationCap
    if (t.includes('gold') || t.includes('jewelry')) return LucideIcons.Gem
    if (t.includes('travel') || t.includes('trip') || t.includes('vacation'))
      return LucideIcons.Plane
    return LucideIcons.Compass
  }

  // Goal Color Mapper based on index/category for rich UI
  const getGoalColor = (idx) => {
    const colors = ['#7C3AED', '#10B981', '#F59E0B', '#EF4444', '#3B82F6', '#EC4899']
    return colors[idx % colors.length]
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: shouldReduceMotion ? 0 : 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="flex flex-col gap-6 w-full text-left"
    >
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex flex-col gap-2">
          <h3 className="text-lg font-black text-text-primary uppercase tracking-wider leading-none">
            Long-term Savings Goals
          </h3>
          <p className="text-xs font-bold text-text-muted">
            Configure, manage, and track progress targets for savings and investments.
          </p>
        </div>
        <Button
          variant="gradient"
          size="sm"
          onClick={handleAddClick}
          className="rounded-xl font-bold text-xs gap-1.5 shadow-button"
          iconLeft={<LucideIcons.Plus className="h-4 w-4" />}
        >
          Create Goal Target
        </Button>
      </div>

      <DashboardGrid>
        {items.length > 0 ? (
          items.map((goal, idx) => {
            const GoalIcon = getGoalIcon(goal.title)
            const targetAmt = parseFloat(goal.target_amount)
            const currentAmt = parseFloat(goal.current_amount)
            const pct = targetAmt > 0 ? Math.round((currentAmt / targetAmt) * 100) : 0
            const remaining = Math.max(0, targetAmt - currentAmt)
            const goalColor = getGoalColor(idx)

            return (
              <motion.div
                key={goal.id}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: idx * 0.05 }}
                className="lg:col-span-6 md:col-span-1"
              >
                <div className="clay-surface bg-card border border-white/60 dark:border-white/5 p-5 flex gap-4 shadow-card hover:border-primary/20 transition-all duration-200 h-full relative group">
                  {/* SVG Progress Circle */}
                  <div className="relative h-16 w-16 flex items-center justify-center shrink-0">
                    <svg className="h-full w-full transform -rotate-90" viewBox="0 0 36 36">
                      <path
                        className="text-muted"
                        strokeWidth="3.5"
                        stroke="currentColor"
                        fill="transparent"
                        d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                      />
                      <path
                        className="transition-all duration-500"
                        strokeWidth="3.5"
                        strokeDasharray={`${pct}, 100`}
                        strokeLinecap="round"
                        stroke={goalColor}
                        fill="transparent"
                        d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                      />
                    </svg>
                    <div className="absolute inset-0 flex items-center justify-center text-white shrink-0 p-3 rounded-full">
                      <div
                        className="h-8 w-8 rounded-full flex items-center justify-center text-white shadow-xs border"
                        style={{ background: goalColor }}
                      >
                        <GoalIcon className="h-4 w-4" />
                      </div>
                    </div>
                  </div>

                  {/* Info Text */}
                  <div className="flex-1 flex flex-col justify-between text-left gap-1 min-w-0">
                    <div className="flex justify-between items-center text-xs font-black text-text-primary leading-none gap-2">
                      <span className="truncate">{goal.title}</span>
                      <span className="text-[10px] font-bold text-text-muted shrink-0">
                        Target:{' '}
                        {goal.target_date
                          ? new Date(goal.target_date).toLocaleDateString('en-US', {
                              month: 'short',
                              year: 'numeric',
                            })
                          : 'Flexible'}
                      </span>
                    </div>

                    <div className="flex justify-between items-center text-[10px] font-bold text-text-secondary mt-2">
                      <span>
                        ₹{currentAmt.toLocaleString('en-IN')} / ₹{targetAmt.toLocaleString('en-IN')}
                      </span>
                      <span className="font-black text-text-primary">{pct}%</span>
                    </div>

                    <div className="w-full bg-muted h-1.5 rounded-full overflow-hidden border mt-1">
                      <div
                        className="h-full rounded-full transition-all duration-500"
                        style={{ width: `${Math.min(pct, 100)}%`, backgroundColor: goalColor }}
                      />
                    </div>

                    <div className="flex justify-between items-center text-[9px] font-bold text-text-muted uppercase tracking-wider mt-1.5 border-t border-border/40 pt-1.5">
                      <span>Remaining: ₹{remaining.toLocaleString('en-IN')}</span>
                      <div className="flex items-center gap-1.5">
                        <button
                          onClick={() => handleEditClick(goal)}
                          className="p-1 rounded text-text-muted hover:text-primary hover:bg-primary/10 transition-colors cursor-pointer"
                          title="Edit Goal"
                        >
                          <LucideIcons.Edit2 className="h-3.5 w-3.5" />
                        </button>
                        <button
                          onClick={() => setDeleteTargetId(goal.id)}
                          className="p-1 rounded text-text-muted hover:text-danger hover:bg-danger/10 transition-colors cursor-pointer"
                          title="Remove Goal"
                        >
                          <LucideIcons.Trash2 className="h-3.5 w-3.5" />
                        </button>
                        <Badge
                          variant="secondary"
                          className="text-[7px] font-bold px-1 py-0.5 rounded capitalize"
                        >
                          {goal.status.toLowerCase()}
                        </Badge>
                      </div>
                    </div>
                  </div>
                </div>
              </motion.div>
            )
          })
        ) : (
          <div className="lg:col-span-12 text-center py-12 bg-muted/10 border border-dashed border-border rounded-2xl select-none">
            <LucideIcons.Inbox className="h-10 w-10 text-text-muted mx-auto stroke-[1.5]" />
            <h4 className="text-sm font-black text-text-muted uppercase mt-3 tracking-wider">
              No savings goals
            </h4>
            <p className="text-xs font-bold text-text-muted/65 mt-1">
              Configure goals like buying a house, emergency fund or travel targets.
            </p>
          </div>
        )}
      </DashboardGrid>

      {/* Creation/Edit Modal */}
      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} size="md">
        <form onSubmit={handleFormSubmit} className="flex flex-col h-full">
          <ModalHeader onClose={() => setIsModalOpen(false)}>
            <span className="text-lg font-black text-text-primary uppercase tracking-wider">
              {editingItem ? 'Edit Savings Goal' : 'Create Savings Goal'}
            </span>
            <span className="text-[10px] font-bold text-text-muted">
              Set targets for future events, acquisitions or SIPs
            </span>
          </ModalHeader>
          <ModalBody className="flex flex-col gap-4">
            {formError && (
              <div className="p-3 bg-danger/10 border border-danger/25 text-danger text-xs font-bold rounded-xl flex items-center gap-2">
                <LucideIcons.AlertTriangle className="h-4 w-4 shrink-0" />
                <span>{formError}</span>
              </div>
            )}

            <div className="flex flex-col gap-1.5 text-left">
              <FieldLabel htmlFor="goal-title">Goal Title / Name</FieldLabel>
              <Input
                id="goal-title"
                value={formTitle}
                onChange={(e) => setFormTitle(e.target.value)}
                placeholder="e.g. New Electric Car, House Downpayment"
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="flex flex-col gap-1.5 text-left">
                <FieldLabel htmlFor="goal-target">Target Amount (₹)</FieldLabel>
                <Input
                  id="goal-target"
                  type="number"
                  value={formTarget}
                  onChange={(e) => setFormTarget(e.target.value)}
                  placeholder="e.g. 500000"
                  min="1"
                  required
                />
              </div>

              <div className="flex flex-col gap-1.5 text-left">
                <FieldLabel htmlFor="goal-current">Currently Saved (₹)</FieldLabel>
                <Input
                  id="goal-current"
                  type="number"
                  value={formCurrent}
                  onChange={(e) => setFormCurrent(e.target.value)}
                  placeholder="e.g. 25000"
                  min="0"
                  required
                />
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div className="flex flex-col gap-1.5 text-left col-span-2">
                <FieldLabel htmlFor="goal-date">Target Completion Date</FieldLabel>
                <Input
                  id="goal-date"
                  type="date"
                  value={formDate}
                  onChange={(e) => setFormDate(e.target.value)}
                />
              </div>

              <div className="flex flex-col gap-1.5 text-left">
                <FieldLabel htmlFor="goal-priority">Priority</FieldLabel>
                <Select
                  id="goal-priority"
                  value={formPriority}
                  onChange={(e) => setFormPriority(e.target.value)}
                >
                  <option value="1">Low</option>
                  <option value="2">Medium-Low</option>
                  <option value="3">Medium</option>
                  <option value="4">Medium-High</option>
                  <option value="5">High</option>
                </Select>
              </div>
            </div>

            <div className="flex flex-col gap-1.5 text-left">
              <FieldLabel htmlFor="goal-status">Goal Status</FieldLabel>
              <Select
                id="goal-status"
                value={formStatus}
                onChange={(e) => setFormStatus(e.target.value)}
              >
                <option value="ACTIVE">Active</option>
                <option value="PAUSED">Paused</option>
                <option value="COMPLETED">Completed</option>
                <option value="CANCELLED">Cancelled</option>
              </Select>
            </div>
          </ModalBody>
          <ModalFooter>
            <Button
              type="button"
              variant="secondary"
              onClick={() => setIsModalOpen(false)}
              className="rounded-xl font-bold text-xs"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="gradient"
              className="rounded-xl font-bold text-xs"
              disabled={createGoalMutation.isPending || updateGoalMutation.isPending}
            >
              {editingItem
                ? updateGoalMutation.isPending
                  ? 'Updating...'
                  : 'Update Goal'
                : createGoalMutation.isPending
                  ? 'Establishing Goal...'
                  : 'Establish Goal'}
            </Button>
          </ModalFooter>
        </form>
      </Modal>

      {/* Confirmation Dialog */}
      <ConfirmationDialog
        isOpen={deleteTargetId !== null}
        onClose={() => setDeleteTargetId(null)}
        onConfirm={handleDeleteConfirm}
        title="Delete Savings Goal?"
        description="Are you sure you want to delete this savings target? This will remove progress tracking from your dashboard."
        confirmText={deleteGoalMutation.isPending ? 'Deleting...' : 'Delete Goal'}
        cancelText="Cancel"
        variant="destructive"
      />
    </motion.div>
  )
}

export default Goals
