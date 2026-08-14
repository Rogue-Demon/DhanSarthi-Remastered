import React, { useState } from 'react'
import {
  useProfile,
  useLiabilities,
  useCreateLiability,
  useDeleteLiability,
  useUpdateLiability,
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

export function Liabilities() {
  const { profile } = useProfile()
  const shouldReduceMotion = useReducedMotion()

  // Queries & Mutations
  const { data: liabilitiesData, isLoading } = useLiabilities()
  const createLiabilityMutation = useCreateLiability()
  const updateLiabilityMutation = useUpdateLiability()
  const deleteLiabilityMutation = useDeleteLiability()

  // Modal & Dialog state
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [deleteTargetId, setDeleteTargetId] = useState(null)
  const [editingItem, setEditingItem] = useState(null)

  // Form state
  const [formName, setFormName] = useState('')
  const [formType, setFormType] = useState('PERSONAL_DEBT')
  const [formBalance, setFormBalance] = useState('')
  const [formRate, setFormRate] = useState('')
  const [formError, setFormError] = useState(null)

  const liabilityTypes = [
    { value: 'PERSONAL_DEBT', label: 'Personal Loan' },
    { value: 'CREDIT_CARD', label: 'Credit Card Debt' },
    { value: 'HOME_LOAN', label: 'Home Loan / Mortgage' },
    { value: 'EDUCATION_LOAN', label: 'Education / Student Loan' },
    { value: 'BUSINESS', label: 'Business Credit Line' },
    { value: 'OTHER', label: 'Other Liability' },
  ]

  const handleAddClick = () => {
    setEditingItem(null)
    setFormName('')
    setFormType('PERSONAL_DEBT')
    setFormBalance('')
    setFormRate('')
    setFormError(null)
    setIsModalOpen(true)
  }

  const handleEditClick = (item) => {
    setEditingItem(item)
    setFormName(item.name)
    setFormType(item.liability_type)
    setFormBalance(item.outstanding_balance.toString())
    setFormRate(item.interest_rate_percent.toString())
    setFormError(null)
    setIsModalOpen(true)
  }

  const handleFormSubmit = async (e) => {
    e.preventDefault()
    setFormError(null)

    const balanceVal = parseFloat(formBalance)
    const rateVal = parseFloat(formRate || '0')

    if (!formName.trim()) {
      setFormError('Liability name is required.')
      return
    }
    if (isNaN(balanceVal) || balanceVal <= 0) {
      setFormError('Balance must be a positive number.')
      return
    }
    if (isNaN(rateVal) || rateVal < 0) {
      setFormError('Interest rate must be non-negative.')
      return
    }

    const payload = {
      name: formName,
      liability_type: formType,
      outstanding_balance: balanceVal,
      interest_rate_percent: rateVal,
    }

    try {
      if (editingItem) {
        await updateLiabilityMutation.mutateAsync({
          id: editingItem.id,
          data: payload,
        })
      } else {
        await createLiabilityMutation.mutateAsync(payload)
      }
      setIsModalOpen(false)
    } catch (err) {
      setFormError(err.message || 'Failed to register liability.')
    }
  }

  const handleDeleteConfirm = async () => {
    if (!deleteTargetId) return
    try {
      await deleteLiabilityMutation.mutateAsync(deleteTargetId)
      setDeleteTargetId(null)
    } catch (err) {
      alert(err.message || 'Failed to delete liability.')
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

  const items = liabilitiesData?.items || []

  const getLiabilityIcon = (type) => {
    switch (type) {
      case 'CREDIT_CARD':
        return LucideIcons.CreditCard
      case 'HOME_LOAN':
        return LucideIcons.Home
      case 'EDUCATION_LOAN':
        return LucideIcons.GraduationCap
      case 'BUSINESS':
        return LucideIcons.Briefcase
      default:
        return LucideIcons.Handshake
    }
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
            Outstanding Liabilities
          </h3>
          <p className="text-xs font-bold text-text-muted">
            Monitor active loan liabilities, credit cards, outstanding invoices, and interest rates.
          </p>
        </div>
        <Button
          variant="gradient"
          size="sm"
          onClick={handleAddClick}
          className="rounded-xl font-bold text-xs gap-1.5 shadow-button"
          iconLeft={<LucideIcons.Plus className="h-4 w-4" />}
        >
          Add Liability
        </Button>
      </div>

      <DashboardGrid>
        {items.length > 0 ? (
          items.map((item, idx) => {
            const Icon = getLiabilityIcon(item.liability_type)

            return (
              <motion.div
                key={item.id}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: idx * 0.05 }}
                className="lg:col-span-6 md:col-span-1"
              >
                <div className="clay-surface bg-card p-5 border border-white/60 dark:border-white/5 shadow-card flex items-center justify-between gap-4 select-none relative group h-full">
                  {/* Visual bar */}
                  <div className="absolute left-0 top-0 bottom-0 w-1 bg-danger transition-all duration-300 group-hover:w-1.5" />

                  <div className="flex flex-col gap-1.5 pl-2 text-left flex-1 min-w-0">
                    <span className="text-xs font-black text-text-primary group-hover:text-primary transition-colors duration-200 truncate">
                      {item.name}
                    </span>
                    <span className="text-2xl font-black text-text-primary tracking-tight leading-none mt-1 truncate">
                      ₹{parseFloat(item.outstanding_balance).toLocaleString('en-IN')}
                    </span>
                    <div className="flex items-center gap-2 mt-1">
                      <Badge
                        variant="secondary"
                        className="text-[8px] font-bold py-0.5 px-1 bg-danger/10 text-danger border-danger/15 rounded"
                      >
                        Rate: {item.interest_rate_percent}%
                      </Badge>
                      <span className="text-[10px] font-bold text-text-muted truncate capitalize">
                        {item.liability_type.replace(/_/g, ' ').toLowerCase()}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <button
                      onClick={() => handleEditClick(item)}
                      className="p-2 rounded-xl text-text-muted hover:text-primary hover:bg-primary/10 border border-transparent hover:border-primary/10 transition-all duration-200 cursor-pointer"
                      title="Edit debt"
                    >
                      <LucideIcons.Edit2 className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => setDeleteTargetId(item.id)}
                      className="p-2 rounded-xl text-text-muted hover:text-danger hover:bg-danger/10 border border-transparent hover:border-danger/10 transition-all duration-200 cursor-pointer"
                      title="Remove debt"
                    >
                      <LucideIcons.Trash2 className="h-4 w-4" />
                    </button>
                    <div className="p-3.5 rounded-2xl flex items-center justify-center border border-white/40 dark:border-white/5 bg-danger/10 text-danger shadow-xs">
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
              No liabilities registered
            </h4>
            <p className="text-xs font-bold text-text-muted/65 mt-1">
              Add home loans, student loans, or credit cards to monitor DTI limits.
            </p>
          </div>
        )}
      </DashboardGrid>

      {/* Creation/Edit Modal */}
      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} size="md">
        <form onSubmit={handleFormSubmit} className="flex flex-col h-full">
          <ModalHeader onClose={() => setIsModalOpen(false)}>
            <span className="text-lg font-black text-text-primary uppercase tracking-wider">
              {editingItem ? 'Edit Debt/Liability' : 'Add Debt/Liability'}
            </span>
            <span className="text-[10px] font-bold text-text-muted">
              Register loans or credit obligations
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
              <FieldLabel htmlFor="debt-name">Debt Name / Title</FieldLabel>
              <Input
                id="debt-name"
                value={formName}
                onChange={(e) => setFormName(e.target.value)}
                placeholder="e.g. ICICI Credit Card, Education Loan"
                required
              />
            </div>

            <div className="flex flex-col gap-1.5 text-left">
              <FieldLabel htmlFor="debt-balance">Outstanding Balance (₹)</FieldLabel>
              <Input
                id="debt-balance"
                type="number"
                value={formBalance}
                onChange={(e) => setFormBalance(e.target.value)}
                placeholder="e.g. 75000"
                min="1"
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="flex flex-col gap-1.5 text-left">
                <FieldLabel htmlFor="debt-type">Liability Type</FieldLabel>
                <Select
                  id="debt-type"
                  value={formType}
                  onChange={(e) => setFormType(e.target.value)}
                >
                  {liabilityTypes.map((type) => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </Select>
              </div>

              <div className="flex flex-col gap-1.5 text-left">
                <FieldLabel htmlFor="debt-rate">Interest Rate (% p.a.)</FieldLabel>
                <Input
                  id="debt-rate"
                  type="number"
                  step="0.01"
                  value={formRate}
                  onChange={(e) => setFormRate(e.target.value)}
                  placeholder="e.g. 12.5"
                  min="0"
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
              disabled={createLiabilityMutation.isPending || updateLiabilityMutation.isPending}
            >
              {editingItem
                ? updateLiabilityMutation.isPending
                  ? 'Updating...'
                  : 'Update Debt'
                : createLiabilityMutation.isPending
                  ? 'Saving Debt...'
                  : 'Register Debt'}
            </Button>
          </ModalFooter>
        </form>
      </Modal>

      {/* Confirmation Dialog */}
      <ConfirmationDialog
        isOpen={deleteTargetId !== null}
        onClose={() => setDeleteTargetId(null)}
        onConfirm={handleDeleteConfirm}
        title="Remove Debt entry?"
        description="Are you sure you want to remove this liability record? This will adjust your total debt balance."
        confirmText={deleteLiabilityMutation.isPending ? 'Removing...' : 'Remove Debt'}
        cancelText="Cancel"
        variant="destructive"
      />
    </motion.div>
  )
}

export default Liabilities
