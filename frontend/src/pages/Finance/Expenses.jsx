import React, { useState } from 'react'
import {
  useProfile,
  useExpenses,
  useCreateExpense,
  useDeleteExpense,
  useUpdateExpense,
  useBudgets,
  useDashboardData,
} from '@/hooks'
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

export function Expenses() {
  const { profile } = useProfile()
  const shouldReduceMotion = useReducedMotion()

  // Queries & Mutations
  const { data: expenseData, isLoading: expensesLoading } = useExpenses()
  const { data: budgetsData, isLoading: budgetsLoading } = useBudgets()
  const { data: dashboardData, isLoading: dashLoading } = useDashboardData()
  const createExpenseMutation = useCreateExpense()
  const updateExpenseMutation = useUpdateExpense()
  const deleteExpenseMutation = useDeleteExpense()

  // Modal & Dialog state
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [deleteTargetId, setDeleteTargetId] = useState(null)
  const [editingItem, setEditingItem] = useState(null)

  // Form state
  const [formCategory, setFormCategory] = useState('Groceries')
  const [formAmount, setFormAmount] = useState('')
  const [formDescription, setFormDescription] = useState('')
  const [formDate, setFormDate] = useState(new Date().toISOString().split('T')[0])
  const [formFrequency, setFormFrequency] = useState('ONE_TIME')
  const [formError, setFormError] = useState(null)

  // Categories list options
  const expenseCategories = [
    'Food',
    'Groceries',
    'Rent',
    'Utilities',
    'Entertainment',
    'Health',
    'Education',
    'Other',
  ]

  const handleAddClick = () => {
    setEditingItem(null)
    setFormCategory('Groceries')
    setFormAmount('')
    setFormDescription('')
    setFormDate(new Date().toISOString().split('T')[0])
    setFormFrequency('ONE_TIME')
    setFormError(null)
    setIsModalOpen(true)
  }

  const handleEditClick = (item) => {
    setEditingItem(item)
    setFormCategory(item.category)
    setFormAmount(item.amount.toString())
    setFormDescription(item.description || '')
    setFormDate(item.expense_date)
    setFormFrequency(item.frequency)
    setFormError(null)
    setIsModalOpen(true)
  }

  const handleFormSubmit = async (e) => {
    e.preventDefault()
    setFormError(null)

    // Validation
    const amountVal = parseFloat(formAmount)
    if (isNaN(amountVal) || amountVal <= 0) {
      setFormError('Amount must be a positive number.')
      return
    }
    if (!formDate) {
      setFormError('Transaction date is required.')
      return
    }

    const payload = {
      category: formCategory,
      amount: amountVal,
      description: formDescription || formCategory,
      expense_date: formDate,
      frequency: formFrequency,
      currency: 'INR',
    }

    try {
      if (editingItem) {
        await updateExpenseMutation.mutateAsync({
          id: editingItem.id,
          data: payload,
        })
      } else {
        await createExpenseMutation.mutateAsync(payload)
      }
      setIsModalOpen(false)
    } catch (err) {
      setFormError(err.message || 'Failed to submit expense transaction.')
    }
  }

  const handleDeleteConfirm = async () => {
    if (!deleteTargetId) return
    try {
      await deleteExpenseMutation.mutateAsync(deleteTargetId)
      setDeleteTargetId(null)
    } catch (err) {
      alert(err.message || 'Failed to delete record.')
    }
  }

  if (expensesLoading || budgetsLoading || dashLoading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 w-full animate-pulse">
        <div className="h-28 bg-muted/20 rounded-2xl border" />
        <div className="h-28 bg-muted/20 rounded-2xl border" />
        <div className="h-28 bg-muted/20 rounded-2xl border" />
      </div>
    )
  }

  const items = expenseData?.items || []
  const budgets = budgetsData?.items || []
  const spentByCategory = dashboardData?.cash_flow?.expense_by_category || {}

  const getSpentForCategory = (catName) => {
    const keys = Object.keys(spentByCategory)
    const matchedKey = keys.find((k) => k.toLowerCase() === catName.toLowerCase())
    return matchedKey ? parseFloat(spentByCategory[matchedKey]) : 0
  }

  // Color mapping helper for visual categories
  const getCategoryColor = (catName) => {
    const map = {
      food: '#EF4444',
      groceries: '#F59E0B',
      rent: '#3B82F6',
      utilities: '#06B6D4',
      entertainment: '#8B5CF6',
      health: '#10B981',
      education: '#EC4899',
      other: '#6B7280',
    }
    return map[catName.toLowerCase()] || '#7C3AED'
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
            Outbound Expenditures
          </h3>
          <p className="text-xs font-bold text-text-muted">
            Track expenses per budget category and verify monthly spent ratios.
          </p>
        </div>
        <Button
          variant="gradient"
          size="sm"
          onClick={handleAddClick}
          className="rounded-xl font-bold text-xs gap-1.5 shadow-button"
          iconLeft={<LucideIcons.Plus className="h-4 w-4" />}
        >
          Add Expense
        </Button>
      </div>

      <DashboardGrid>
        {budgets.length > 0 ? (
          budgets.map((budget, idx) => {
            const spentVal = getSpentForCategory(budget.category)
            const budgetVal = parseFloat(budget.amount)
            const pct = budgetVal > 0 ? Math.round((spentVal / budgetVal) * 100) : 0
            const categoryColor = getCategoryColor(budget.category)

            return (
              <motion.div
                key={budget.id}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: idx * 0.05 }}
                className="lg:col-span-4 md:col-span-1"
              >
                <div className="clay-surface bg-card p-5 border border-white/60 dark:border-white/5 shadow-card flex flex-col justify-between gap-4 relative group h-full">
                  {/* Category Header */}
                  <div className="flex items-center gap-3">
                    <div
                      className="p-2 rounded-xl flex items-center justify-center shrink-0 border shadow-xs"
                      style={{
                        background: `${categoryColor}12`,
                        color: categoryColor,
                        borderColor: `${categoryColor}25`,
                      }}
                    >
                      <LucideIcons.Compass className="h-4.5 w-4.5 stroke-[2.2]" />
                    </div>
                    <div className="flex flex-col text-left">
                      <span className="text-xs font-black text-text-primary group-hover:text-primary transition-colors duration-200 capitalize">
                        {budget.category.toLowerCase()}
                      </span>
                      <span className="text-[10px] font-bold text-text-muted mt-0.5">
                        Budget limit: ₹{budgetVal.toLocaleString('en-IN')}
                      </span>
                    </div>
                  </div>

                  {/* Progress bar info */}
                  <div className="flex flex-col gap-1.5 mt-2">
                    <div className="flex justify-between items-center text-[10px] font-semibold text-text-secondary leading-none">
                      <span>Spent: ₹{spentVal.toLocaleString('en-IN')}</span>
                      <span className="font-bold text-text-primary">{pct}%</span>
                    </div>
                    <div className="w-full bg-muted h-2 rounded-full overflow-hidden border border-white/60 shadow-inner">
                      <div
                        className="h-full rounded-full transition-all duration-500"
                        style={{ width: `${Math.min(pct, 100)}%`, backgroundColor: categoryColor }}
                      />
                    </div>
                  </div>
                </div>
              </motion.div>
            )
          })
        ) : (
          <div className="lg:col-span-12 text-center py-6 bg-muted/10 border border-dashed border-border rounded-2xl select-none">
            <h4 className="text-xs font-black text-text-muted uppercase tracking-wider">
              No budgets configured
            </h4>
            <p className="text-[10px] font-bold text-text-muted/65 mt-1">
              Configure category limits under the Budget tab to see tracking bars.
            </p>
          </div>
        )}

        {/* Expenses List Timeline */}
        <WidgetContainer title="Recorded Expense Entries" icon="History" sizeClass="lg:col-span-12">
          <div className="flex flex-col gap-3 py-2">
            {items.length > 0 ? (
              items.map((item, idx) => (
                <div
                  key={item.id}
                  className="flex items-center justify-between p-3 rounded-xl bg-muted/30 border border-border/80 text-xs font-semibold text-text-secondary hover:border-primary/20 transition-all duration-200"
                >
                  <div
                    className="flex flex-col gap-0.5 text-left border-l-2 pl-2"
                    style={{ borderColor: getCategoryColor(item.category) }}
                  >
                    <span className="font-extrabold text-text-primary">
                      {item.description || item.category}
                    </span>
                    <span className="text-[10px] font-bold text-text-muted">
                      {new Date(item.expense_date).toLocaleDateString('en-US', {
                        month: 'short',
                        day: 'numeric',
                        year: 'numeric',
                      })}{' '}
                      • {item.frequency.replace('_', ' ').toLowerCase()}
                    </span>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className="font-extrabold text-text-primary">
                      ₹{parseFloat(item.amount).toLocaleString('en-IN')}
                    </span>
                    <button
                      onClick={() => handleEditClick(item)}
                      className="p-1.5 rounded-lg text-text-muted hover:text-primary hover:bg-primary/10 border border-transparent hover:border-primary/10 transition-all duration-200 cursor-pointer"
                      title="Edit expense"
                    >
                      <LucideIcons.Edit2 className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => setDeleteTargetId(item.id)}
                      className="p-1.5 rounded-lg text-text-muted hover:text-danger hover:bg-danger/10 border border-transparent hover:border-danger/10 transition-all duration-200 cursor-pointer"
                      title="Delete expense"
                    >
                      <LucideIcons.Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              ))
            ) : (
              <span className="text-xs font-bold text-text-muted py-6 text-center block">
                No expense records logged yet.
              </span>
            )}
          </div>
        </WidgetContainer>
      </DashboardGrid>

      {/* Creation/Edit Modal */}
      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} size="md">
        <form onSubmit={handleFormSubmit} className="flex flex-col h-full">
          <ModalHeader onClose={() => setIsModalOpen(false)}>
            <span className="text-lg font-black text-text-primary uppercase tracking-wider">
              {editingItem ? 'Edit Expense Outflow' : 'Log Expense Outflow'}
            </span>
            <span className="text-[10px] font-bold text-text-muted">
              Record outbound transaction costs
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
              <FieldLabel htmlFor="expense-desc">Description / Title</FieldLabel>
              <Input
                id="expense-desc"
                value={formDescription}
                onChange={(e) => setFormDescription(e.target.value)}
                placeholder="e.g. Monthly Rent, Grocery run"
              />
            </div>

            <div className="flex flex-col gap-1.5 text-left">
              <FieldLabel htmlFor="expense-amount">Amount (₹)</FieldLabel>
              <Input
                id="expense-amount"
                type="number"
                value={formAmount}
                onChange={(e) => setFormAmount(e.target.value)}
                placeholder="e.g. 1500"
                min="1"
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="flex flex-col gap-1.5 text-left">
                <FieldLabel htmlFor="expense-category">Category</FieldLabel>
                <Select
                  id="expense-category"
                  value={formCategory}
                  onChange={(e) => setFormCategory(e.target.value)}
                >
                  {expenseCategories.map((cat) => (
                    <option key={cat} value={cat}>
                      {cat}
                    </option>
                  ))}
                </Select>
              </div>

              <div className="flex flex-col gap-1.5 text-left">
                <FieldLabel htmlFor="expense-frequency">Frequency</FieldLabel>
                <Select
                  id="expense-frequency"
                  value={formFrequency}
                  onChange={(e) => setFormFrequency(e.target.value)}
                >
                  <option value="ONE_TIME">One Time</option>
                  <option value="WEEKLY">Weekly</option>
                  <option value="MONTHLY">Monthly</option>
                  <option value="YEARLY">Yearly</option>
                </Select>
              </div>
            </div>

            <div className="flex flex-col gap-1.5 text-left">
              <FieldLabel htmlFor="expense-date">Expense Date</FieldLabel>
              <Input
                id="expense-date"
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
              disabled={createExpenseMutation.isPending || updateExpenseMutation.isPending}
            >
              {editingItem
                ? updateExpenseMutation.isPending
                  ? 'Updating...'
                  : 'Update Expense'
                : createExpenseMutation.isPending
                  ? 'Logging Outflow...'
                  : 'Record Expense'}
            </Button>
          </ModalFooter>
        </form>
      </Modal>

      {/* Confirmation Dialog */}
      <ConfirmationDialog
        isOpen={deleteTargetId !== null}
        onClose={() => setDeleteTargetId(null)}
        onConfirm={handleDeleteConfirm}
        title="Delete Expense entry?"
        description="Are you sure you want to delete this expenditure? This will update category spent progress instantly."
        confirmText={deleteExpenseMutation.isPending ? 'Deleting...' : 'Delete Entry'}
        cancelText="Cancel"
        variant="destructive"
      />
    </motion.div>
  )
}

export default Expenses
