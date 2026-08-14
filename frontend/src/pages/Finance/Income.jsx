import React, { useState } from 'react'
import { useProfile, useIncome, useCreateIncome, useDeleteIncome, useUpdateIncome } from '@/hooks'
import { motion, useReducedMotion } from 'framer-motion'
import { DashboardGrid, WidgetContainer } from '@/components/dashboard'
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

export function Income() {
  const { profile } = useProfile()
  const shouldReduceMotion = useReducedMotion()

  // Queries & Mutations
  const { data: incomeData, isLoading } = useIncome()
  const createIncomeMutation = useCreateIncome()
  const updateIncomeMutation = useUpdateIncome()
  const deleteIncomeMutation = useDeleteIncome()

  // Modal & Dialog state
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [deleteTargetId, setDeleteTargetId] = useState(null)
  const [editingItem, setEditingItem] = useState(null)

  // Form state
  const [formSource, setFormSource] = useState('')
  const [formAmount, setFormAmount] = useState('')
  const [formCategory, setFormCategory] = useState('Salary')
  const [formDate, setFormDate] = useState(new Date().toISOString().split('T')[0])
  const [formFrequency, setFormFrequency] = useState('MONTHLY')
  const [formError, setFormError] = useState(null)

  // Categories list options
  const incomeCategories = [
    'Salary',
    'Freelance',
    'Investment',
    'Stipend',
    'Gift',
    'Refund',
    'Other',
  ]

  const handleAddClick = () => {
    setEditingItem(null)
    setFormSource('')
    setFormAmount('')
    setFormCategory('Salary')
    setFormDate(new Date().toISOString().split('T')[0])
    setFormFrequency('MONTHLY')
    setFormError(null)
    setIsModalOpen(true)
  }

  const handleEditClick = (item) => {
    setEditingItem(item)
    setFormSource(item.source)
    setFormAmount(item.amount.toString())
    setFormCategory(item.category)
    setFormDate(item.income_date)
    setFormFrequency(item.frequency)
    setFormError(null)
    setIsModalOpen(true)
  }

  const handleFormSubmit = async (e) => {
    e.preventDefault()
    setFormError(null)

    // Validation
    const amountVal = parseFloat(formAmount)
    if (!formSource.trim()) {
      setFormError('Source is a required field.')
      return
    }
    if (isNaN(amountVal) || amountVal <= 0) {
      setFormError('Amount must be a positive number.')
      return
    }
    if (!formDate) {
      setFormError('Credit date is required.')
      return
    }

    const payload = {
      source: formSource,
      amount: amountVal,
      income_date: formDate,
      category: formCategory,
      frequency: formFrequency,
      currency: 'INR',
    }

    try {
      if (editingItem) {
        await updateIncomeMutation.mutateAsync({
          id: editingItem.id,
          data: payload,
        })
      } else {
        await createIncomeMutation.mutateAsync(payload)
      }
      setIsModalOpen(false)
    } catch (err) {
      setFormError(err.message || 'Failed to submit credit transaction.')
    }
  }

  const handleDeleteConfirm = async () => {
    if (!deleteTargetId) return
    try {
      await deleteIncomeMutation.mutateAsync(deleteTargetId)
      setDeleteTargetId(null)
    } catch (err) {
      alert(err.message || 'Failed to delete record.')
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

  const items = incomeData?.items || []

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
            Inbound Income Streams
          </h3>
          <p className="text-xs font-bold text-text-muted">
            Detailed breakdown of your incoming credits and active salary pipelines.
          </p>
        </div>
        <Button
          variant="gradient"
          size="sm"
          onClick={handleAddClick}
          className="rounded-xl font-bold text-xs gap-1.5 shadow-button"
          iconLeft={<LucideIcons.Plus className="h-4 w-4" />}
        >
          Add Income
        </Button>
      </div>

      <DashboardGrid>
        {items.length > 0 ? (
          items.map((item, idx) => {
            const Icon = LucideIcons.ArrowUpRight

            return (
              <motion.div
                key={item.id}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: idx * 0.05 }}
                className="lg:col-span-4 md:col-span-1"
              >
                <div className="clay-surface bg-card p-5 border border-white/60 dark:border-white/5 shadow-card flex items-center justify-between gap-4 relative group overflow-hidden h-full">
                  {/* Visual bar glow accent */}
                  <div className="absolute left-0 top-0 bottom-0 w-1 bg-primary transition-all duration-300 group-hover:w-1.5" />

                  <div className="flex flex-col gap-1.5 pl-2 text-left flex-1 min-w-0">
                    <span className="text-[10px] font-black text-text-muted uppercase tracking-wider truncate">
                      {item.source}
                    </span>
                    <span className="text-2xl font-black text-text-primary tracking-tight leading-none truncate">
                      ₹{parseFloat(item.amount).toLocaleString('en-IN')}
                    </span>
                    <span className="text-[10px] font-bold text-text-secondary truncate capitalize">
                      {item.category.toLowerCase()} (
                      {item.frequency.replace('_', ' ').toLowerCase()})
                    </span>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <button
                      onClick={() => handleEditClick(item)}
                      className="p-2 rounded-xl text-text-muted hover:text-primary hover:bg-primary/10 border border-transparent hover:border-primary/10 transition-all duration-200 cursor-pointer"
                      title="Edit stream"
                    >
                      <LucideIcons.Edit2 className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => setDeleteTargetId(item.id)}
                      className="p-2 rounded-xl text-text-muted hover:text-danger hover:bg-danger/10 border border-transparent hover:border-danger/10 transition-all duration-200 cursor-pointer"
                      title="Delete stream"
                    >
                      <LucideIcons.Trash2 className="h-4 w-4" />
                    </button>
                    <div className="p-3.5 rounded-2xl flex items-center justify-center border border-white/40 dark:border-white/5 bg-primary/10 text-primary shadow-xs">
                      <Icon className="h-5 w-5 stroke-[2px]" />
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
              No income records
            </h4>
            <p className="text-xs font-bold text-text-muted/65 mt-1">
              Configure income streams using the Add Income button.
            </p>
          </div>
        )}

        {/* Premium Chart Placeholder */}
        <WidgetContainer
          title="Income vs Expenses Trends"
          icon="LineChart"
          sizeClass="lg:col-span-12"
        >
          <div className="h-32 w-full rounded-2xl bg-card/65 border border-border/80 relative flex items-end justify-between px-8 pb-3 overflow-hidden mt-2">
            <div className="absolute inset-0 opacity-[0.02] bg-[radial-gradient(#7C3AED_1px,transparent_1px)] [background-size:12px_12px]" />

            <svg
              className="absolute inset-0 w-full h-full text-primary/15"
              preserveAspectRatio="none"
              viewBox="0 0 100 100"
            >
              <path d="M0,90 Q20,60 40,80 T80,40 T100,20 L100,100 Z" fill="currentColor" />
              <path
                d="M0,90 Q20,60 40,80 T80,40 T100,20"
                fill="none"
                stroke="var(--primary)"
                strokeWidth="2"
              />
            </svg>

            {['Apr', 'May', 'Jun', 'Jul', 'Aug'].map((m) => (
              <span key={m} className="text-[9px] font-black text-text-muted z-10">
                {m}
              </span>
            ))}

            <div className="absolute top-3 right-4 flex items-center gap-1.5 text-[10px] font-bold text-text-muted">
              <LucideIcons.Sparkles className="h-3.5 w-3.5 text-accent animate-pulse" />
              <span>Yield forecast is positive</span>
            </div>
          </div>
        </WidgetContainer>
      </DashboardGrid>

      {/* Creation/Edit Modal */}
      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} size="md">
        <form onSubmit={handleFormSubmit} className="flex flex-col h-full">
          <ModalHeader onClose={() => setIsModalOpen(false)}>
            <span className="text-lg font-black text-text-primary uppercase tracking-wider">
              {editingItem ? 'Edit Income Inflow' : 'Log Income Inflow'}
            </span>
            <span className="text-[10px] font-bold text-text-muted">
              Record credit salary pipelines or stipends
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
              <FieldLabel htmlFor="income-source">Income Source / Title</FieldLabel>
              <Input
                id="income-source"
                value={formSource}
                onChange={(e) => setFormSource(e.target.value)}
                placeholder="e.g. Salary, Consulting Fee"
                required
              />
            </div>

            <div className="flex flex-col gap-1.5 text-left">
              <FieldLabel htmlFor="income-amount">Amount (₹)</FieldLabel>
              <Input
                id="income-amount"
                type="number"
                value={formAmount}
                onChange={(e) => setFormAmount(e.target.value)}
                placeholder="e.g. 50000"
                min="1"
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="flex flex-col gap-1.5 text-left">
                <FieldLabel htmlFor="income-category">Category</FieldLabel>
                <Select
                  id="income-category"
                  value={formCategory}
                  onChange={(e) => setFormCategory(e.target.value)}
                >
                  {incomeCategories.map((cat) => (
                    <option key={cat} value={cat}>
                      {cat}
                    </option>
                  ))}
                </Select>
              </div>

              <div className="flex flex-col gap-1.5 text-left">
                <FieldLabel htmlFor="income-frequency">Frequency</FieldLabel>
                <Select
                  id="income-frequency"
                  value={formFrequency}
                  onChange={(e) => setFormFrequency(e.target.value)}
                >
                  <option value="ONE_TIME">One Time</option>
                  <option value="WEEKLY">Weekly</option>
                  <option value="MONTHLY">Monthly</option>
                  <option value="QUARTERLY">Quarterly</option>
                  <option value="YEARLY">Yearly</option>
                </Select>
              </div>
            </div>

            <div className="flex flex-col gap-1.5 text-left">
              <FieldLabel htmlFor="income-date">Credit Date</FieldLabel>
              <Input
                id="income-date"
                type="date"
                value={formDate}
                onChange={(e) => setFormDate(e.target.value)}
                required
              />
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
              disabled={createIncomeMutation.isPending || updateIncomeMutation.isPending}
            >
              {editingItem
                ? updateIncomeMutation.isPending
                  ? 'Updating...'
                  : 'Update Credit'
                : createIncomeMutation.isPending
                  ? 'Logging Inflow...'
                  : 'Record Credit'}
            </Button>
          </ModalFooter>
        </form>
      </Modal>

      {/* Confirmation Dialog */}
      <ConfirmationDialog
        isOpen={deleteTargetId !== null}
        onClose={() => setDeleteTargetId(null)}
        onConfirm={handleDeleteConfirm}
        title="Delete Income Stream?"
        description="Are you sure you want to delete this credit source? This will adjust your total surplus dynamically."
        confirmText={deleteIncomeMutation.isPending ? 'Deleting...' : 'Delete Source'}
        cancelText="Cancel"
        variant="destructive"
      />
    </motion.div>
  )
}

export default Income
