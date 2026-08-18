import React, { useState } from 'react'
import {
  useProfile,
  useBudgets,
  useCreateBudget,
  useDeleteBudget,
  useUpdateBudget,
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

export function Budget() {
  const { profile } = useProfile()
  const shouldReduceMotion = useReducedMotion()

  // Queries & Mutations
  const { data: budgetsData, isLoading: budgetsLoading } = useBudgets()
  const { data: dashboardData, isLoading: dashLoading } = useDashboardData()
  const createBudgetMutation = useCreateBudget()
  const updateBudgetMutation = useUpdateBudget()
  const deleteBudgetMutation = useDeleteBudget()

  // Modal & Dialog state
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [deleteTargetId, setDeleteTargetId] = useState(null)
  const [editingItem, setEditingItem] = useState(null)

  // Form state
  const [formCategory, setFormCategory] = useState('Groceries')
  const [formAmount, setFormAmount] = useState('')
  const [formPeriod, setFormPeriod] = useState('MONTHLY')
  const [formDate, setFormDate] = useState(new Date().toISOString().split('T')[0])
  const [formError, setFormError] = useState(null)

  // Categories list options
  const budgetCategories = [
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
    setFormPeriod('MONTHLY')
    setFormDate(new Date().toISOString().split('T')[0])
    setFormError(null)
    setIsModalOpen(true)
  }

  const handleEditClick = (item) => {
    setEditingItem(item)
    setFormCategory(item.category)
    setFormAmount(item.amount.toString())
    setFormPeriod(item.period)
    setFormDate(item.start_date)
    setFormError(null)
    setIsModalOpen(true)
  }

  const handleFormSubmit = async (e) => {
    e.preventDefault()
    setFormError(null)

    const amountVal = parseFloat(formAmount)
    if (isNaN(amountVal) || amountVal <= 0) {
      setFormError('Limit amount must be a positive number.')
      return
    }
    if (!formDate) {
      setFormError('Start date is required.')
      return
    }

    const payload = {
      category: formCategory,
      amount: amountVal,
      period: formPeriod,
      start_date: formDate,
    }

    try {
      if (editingItem) {
        await updateBudgetMutation.mutateAsync({
          id: editingItem.id,
          data: payload,
        })
      } else {
        await createBudgetMutation.mutateAsync(payload)
      }
      setIsModalOpen(false)
    } catch (err) {
      setFormError(err.message || 'Failed to establish category budget limit.')
    }
  }

  const handleDeleteConfirm = async () => {
    if (!deleteTargetId) return
    try {
      await deleteBudgetMutation.mutateAsync(deleteTargetId)
      setDeleteTargetId(null)
    } catch (err) {
      alert(err.message || 'Failed to delete budget limit.')
    }
  }

  if (budgetsLoading || dashLoading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 w-full animate-pulse">
        <div className="h-28 bg-muted/20 rounded-2xl border" />
        <div className="h-28 bg-muted/20 rounded-2xl border" />
        <div className="h-28 bg-muted/20 rounded-2xl border" />
      </div>
    )
  }

  const items = budgetsData?.items || []
  const spentByCategory = dashboardData?.cash_flow?.expense_by_category || {}

  const getSpentForCategory = (catName) => {
    const keys = Object.keys(spentByCategory)
    const matchedKey = keys.find((k) => k.toLowerCase() === catName.toLowerCase())
    return matchedKey ? parseFloat(spentByCategory[matchedKey]) : 0
  }

  // Calculations
  const totalBudgetLimit = items.reduce((acc, b) => acc + parseFloat(b.amount), 0)
  const totalSpent = items.reduce((acc, b) => acc + getSpentForCategory(b.category), 0)
  const remainingBalance = Math.max(0, totalBudgetLimit - totalSpent)
  const progressPct = totalBudgetLimit > 0 ? Math.round((totalSpent / totalBudgetLimit) * 100) : 0
  const isOverBudget = totalSpent > totalBudgetLimit

  // Category Color Map
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
            Financial Budget Tracker
          </h3>
          <p className="text-xs font-bold text-text-muted">
            Compare total budget limits, actual expenditures, and remaining balances.
          </p>
        </div>
        <Button
          variant="gradient"
          size="sm"
          onClick={handleAddClick}
          className="rounded-xl font-bold text-xs gap-1.5 shadow-button"
          iconLeft={<LucideIcons.Plus className="h-4 w-4" />}
        >
          Set Category Budget
        </Button>
      </div>

      <DashboardGrid>
        {/* Core summary card */}
        <div className="lg:col-span-12 grid grid-cols-1 sm:grid-cols-4 gap-4 bg-muted/20 border border-border/85 p-5 rounded-2xl">
          <div className="flex flex-col">
            <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider">
              Total Budget Limit
            </span>
            <span className="text-xl font-extrabold text-text-primary mt-1">
              ₹{totalBudgetLimit.toLocaleString('en-IN')}
            </span>
          </div>
          <div className="flex flex-col border-l border-border/80 pl-4">
            <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider">
              Spent to Date
            </span>
            <span className="text-xl font-extrabold text-primary mt-1">
              ₹{totalSpent.toLocaleString('en-IN')}
            </span>
          </div>
          <div className="flex flex-col border-l border-border/80 pl-4">
            <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider">
              Remaining Balance
            </span>
            <span className="text-xl font-extrabold text-success mt-1">
              ₹{remainingBalance.toLocaleString('en-IN')}
            </span>
          </div>
          <div className="flex flex-col border-l border-border/80 pl-4 justify-center">
            <Badge
              variant="secondary"
              className={`mr-auto text-[10px] font-black uppercase py-1 px-2.5 rounded border ${isOverBudget ? 'bg-danger/10 border-danger/20 text-danger' : 'bg-success/10 border-success/20 text-success'}`}
            >
              {isOverBudget ? 'OVER BUDGET' : 'ON TRACK'}
            </Badge>
          </div>
        </div>

        {/* Spent Progress Bar */}
        <WidgetContainer
          title="Overall Budget Progress"
          icon="PieChart"
          sizeClass="lg:col-span-4 md:col-span-1"
        >
          <div className="flex flex-col justify-center items-start gap-4 py-2 text-left">
            <div className="flex justify-between items-center w-full text-xs font-bold text-text-secondary leading-none">
              <span>Spent Margin Limit</span>
              <span className="text-primary font-black">{progressPct}% spent</span>
            </div>
            <div className="w-full bg-muted h-3 rounded-full overflow-hidden border border-white/60 shadow-inner">
              <div
                className="bg-gradient-primary h-full rounded-full transition-all duration-500"
                style={{ width: `${Math.min(progressPct, 100)}%` }}
              />
            </div>
            <span className="text-[10px] font-bold text-text-muted leading-relaxed">
              Based on active allocations, you have ₹{remainingBalance.toLocaleString('en-IN')}{' '}
              remaining limit.
            </span>
          </div>
        </WidgetContainer>

        {/* Savings Recommendation */}
        <WidgetContainer
          title="Savings Opportunity"
          icon="TrendingUp"
          sizeClass="lg:col-span-8 md:col-span-2"
        >
          <div className="flex items-start gap-4 py-1 text-left select-none relative group">
            <div className="h-10 w-10 rounded-xl bg-success/15 border border-success/20 text-success flex items-center justify-center shrink-0">
              <LucideIcons.Sparkles className="h-5 w-5" />
            </div>
            <div className="flex flex-col gap-1">
              <span className="text-xs font-black text-text-primary leading-none uppercase">
                AI Recommendation
              </span>
              <p className="text-xs font-semibold text-text-secondary leading-relaxed mt-1">
                By capping utility and dining out categories, you can redirect an estimated{' '}
                <span className="text-success font-extrabold">₹1,500</span> directly to your active
                savings goals!
              </p>
            </div>
          </div>
        </WidgetContainer>

        {/* Budget list entries */}
        <WidgetContainer title="Category Allocations" icon="ListFilter" sizeClass="lg:col-span-12">
          <div className="flex flex-col gap-3 py-2">
            {items.length > 0 ? (
              items.map((budget) => {
                const spent = getSpentForCategory(budget.category)
                const limit = parseFloat(budget.amount)
                const pct = limit > 0 ? Math.round((spent / limit) * 100) : 0

                return (
                  <div
                    key={budget.id}
                    className="flex flex-col sm:flex-row sm:items-center justify-between p-4 rounded-2xl bg-muted/20 border border-border/80 gap-4"
                  >
                    <div className="flex flex-col text-left flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-extrabold text-sm text-text-primary capitalize">
                          {budget.category.toLowerCase()}
                        </span>
                        <Badge
                          variant="secondary"
                          className="text-[8px] font-black uppercase rounded py-0.5 px-1 bg-primary/10 text-primary border-primary/15"
                        >
                          {budget.period.toLowerCase()}
                        </Badge>
                      </div>
                      <div className="w-full bg-muted h-2 rounded-full overflow-hidden border border-white/60 shadow-inner mt-2">
                        <div
                          className="h-full rounded-full transition-all duration-500"
                          style={{
                            width: `${Math.min(pct, 100)}%`,
                            backgroundColor: getCategoryColor(budget.category),
                          }}
                        />
                      </div>
                      <span className="text-[10px] font-bold text-text-muted mt-1">
                        Spent ₹{spent.toLocaleString('en-IN')} of ₹{limit.toLocaleString('en-IN')}{' '}
                        limit ({pct}%)
                      </span>
                    </div>

                    <div className="flex items-center gap-4 shrink-0">
                      <span className="text-xs font-bold text-text-secondary">
                        Remaining: ₹{Math.max(0, limit - spent).toLocaleString('en-IN')}
                      </span>
                      <button
                        onClick={() => handleEditClick(budget)}
                        className="p-1.5 rounded-lg text-text-muted hover:text-primary hover:bg-primary/10 border border-transparent hover:border-primary/10 transition-all duration-200 cursor-pointer"
                        title="Edit budget limit"
                      >
                        <LucideIcons.Edit2 className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => setDeleteTargetId(budget.id)}
                        className="p-1.5 rounded-lg text-text-muted hover:text-danger hover:bg-danger/10 border border-transparent hover:border-danger/10 transition-all duration-200 cursor-pointer"
                        title="Remove budget limit"
                      >
                        <LucideIcons.Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                )
              })
            ) : (
              <span className="text-xs font-bold text-text-muted py-6 text-center block">
                No category budgets established yet.
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
              {editingItem ? 'Edit Category Budget' : 'Set Category Budget'}
            </span>
            <span className="text-[10px] font-bold text-text-muted">
              Enforce monthly spent limits per category
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
              <FieldLabel htmlFor="budget-category">Budget Category</FieldLabel>
              <Select
                id="budget-category"
                value={formCategory}
                onChange={(e) => setFormCategory(e.target.value)}
              >
                {budgetCategories.map((cat) => (
                  <option key={cat} value={cat}>
                    {cat}
                  </option>
                ))}
              </Select>
            </div>

            <div className="flex flex-col gap-1.5 text-left">
              <FieldLabel htmlFor="budget-limit">Budget Limit Amount (₹)</FieldLabel>
              <Input
                id="budget-limit"
                type="number"
                value={formAmount}
                onChange={(e) => setFormAmount(e.target.value)}
                placeholder="e.g. 10000"
                min="1"
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="flex flex-col gap-1.5 text-left">
                <FieldLabel htmlFor="budget-period">Period</FieldLabel>
                <Select
                  id="budget-period"
                  value={formPeriod}
                  onChange={(e) => setFormPeriod(e.target.value)}
                >
                  <option value="WEEKLY">Weekly</option>
                  <option value="MONTHLY">Monthly</option>
                  <option value="YEARLY">Yearly</option>
                  <option value="CUSTOM">Custom</option>
                </Select>
              </div>

              <div className="flex flex-col gap-1.5 text-left">
                <FieldLabel htmlFor="budget-date">Start Date</FieldLabel>
                <Input
                  id="budget-date"
                  type="date"
                  value={formDate}
                  onChange={(e) => setFormDate(e.target.value)}
                  required
                />
              </div>
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
              disabled={createBudgetMutation.isPending || updateBudgetMutation.isPending}
            >
              {editingItem
                ? updateBudgetMutation.isPending
                  ? 'Updating...'
                  : 'Update Limit'
                : createBudgetMutation.isPending
                  ? 'Establishing...'
                  : 'Establish Limit'}
            </Button>
          </ModalFooter>
        </form>
      </Modal>

      {/* Confirmation Dialog */}
      <ConfirmationDialog
        isOpen={deleteTargetId !== null}
        onClose={() => setDeleteTargetId(null)}
        onConfirm={handleDeleteConfirm}
        title="Delete Category Budget?"
        description="Are you sure you want to remove this category budget limit? This will stop progress tracking for this category."
        confirmText={deleteBudgetMutation.isPending ? 'Removing...' : 'Remove Limit'}
        cancelText="Cancel"
        variant="destructive"
      />
    </motion.div>
  )
}

export default Budget
