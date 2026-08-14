import React, { useState } from 'react'
import {
  useProfile,
  useInvestments,
  useCreateInvestment,
  useUpdateInvestment,
  useDeleteInvestment,
} from '@/hooks'
import { getInvestmentsConfig } from '@/config'
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

export function PPF() {
  const { profile } = useProfile()
  const shouldReduceMotion = useReducedMotion()
  const investData = getInvestmentsConfig(profile)

  // Queries and mutations (fetch OTHER types and filter for PPF subtype client-side)
  const { data: investmentsData, isLoading } = useInvestments({ investment_type: 'OTHER' })
  const createMutation = useCreateInvestment()
  const updateMutation = useUpdateInvestment()
  const deleteMutation = useDeleteInvestment()

  // Modal states
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingItem, setEditingItem] = useState(null)
  const [deleteTargetId, setDeleteTargetId] = useState(null)

  // Form states
  const [name, setName] = useState('')
  const [balance, setBalance] = useState('')
  const [annualContribution, setAnnualContribution] = useState('')
  const [interestRate, setInterestRate] = useState('')
  const [maturityDate, setMaturityDate] = useState('')
  const [notes, setNotes] = useState('')

  const handleAddClick = () => {
    setEditingItem(null)
    setName('')
    setBalance('')
    setAnnualContribution('')
    setInterestRate('7.1') // Default PPF rate
    setMaturityDate('')
    setNotes('')
    setIsModalOpen(true)
  }

  const handleEditClick = (item) => {
    setEditingItem(item)
    setName(item.name || '')
    setBalance(item.current_value || '')
    setAnnualContribution(item.investment_metadata?.annual_contribution || '')
    setInterestRate(item.interest_rate ? parseFloat(item.interest_rate * 100).toString() : '7.1')
    setMaturityDate(item.maturity_date || '')
    setNotes(item.notes || '')
    setIsModalOpen(true)
  }

  const handleFormSubmit = async (e) => {
    e.preventDefault()
    const payload = {
      name,
      investment_type: 'OTHER',
      invested_amount: parseFloat(balance) || 0,
      current_value: parseFloat(balance) || 0,
      interest_rate: interestRate ? parseFloat(interestRate) / 100 : null,
      maturity_date: maturityDate || null,
      notes: notes || null,
      investment_metadata: {
        subtype: 'PPF',
        annual_contribution: parseFloat(annualContribution) || 0,
      },
    }

    try {
      if (editingItem) {
        await updateMutation.mutateAsync({ id: editingItem.id, data: payload })
      } else {
        await createMutation.mutateAsync(payload)
      }
      setIsModalOpen(false)
    } catch (err) {
      alert(err.message || 'Failed to save PPF account.')
    }
  }

  const handleDeleteConfirm = async () => {
    if (!deleteTargetId) return
    try {
      await deleteMutation.mutateAsync(deleteTargetId)
      setDeleteTargetId(null)
    } catch (err) {
      alert(err.message || 'Failed to delete PPF account.')
    }
  }

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 gap-6 w-full animate-pulse">
        <div className="h-28 bg-muted/20 rounded-2xl border" />
        <div className="h-28 bg-muted/20 rounded-2xl border" />
      </div>
    )
  }

  const ppfs = (investmentsData?.items || []).filter(
    (item) => item.investment_metadata?.subtype === 'PPF'
  )

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
            Public Provident Fund (PPF)
          </h3>
          <p className="text-xs font-bold text-text-muted">
            Long-term tax-exempt government savings instrument with compound interest accrual.
          </p>
        </div>
        <Button
          variant="gradient"
          size="sm"
          onClick={handleAddClick}
          className="rounded-xl font-bold text-xs gap-1.5 shadow-button"
          iconLeft={<LucideIcons.Plus className="h-4 w-4" />}
        >
          Add PPF
        </Button>
      </div>

      <DashboardGrid>
        {ppfs.length > 0 ? (
          ppfs.map((ppf, idx) => {
            const balanceVal = parseFloat(ppf.current_value || 0)
            const annualContributionVal = parseFloat(
              ppf.investment_metadata?.annual_contribution || 0
            )
            const rate = ppf.interest_rate ? parseFloat(ppf.interest_rate * 100) : 7.1

            return (
              <motion.div
                key={ppf.id}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: idx * 0.05 }}
                className="lg:col-span-12 md:col-span-2"
              >
                <div className="clay-surface bg-card p-6 border border-white/60 dark:border-white/5 shadow-card select-none relative group">
                  <div className="absolute left-0 top-0 bottom-0 w-1 bg-success transition-all duration-300 group-hover:w-1.5" />

                  <div className="grid grid-cols-1 sm:grid-cols-5 gap-6 pl-2 text-left items-center">
                    {/* Account Summary */}
                    <div className="flex flex-col gap-1">
                      <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider">
                        Account
                      </span>
                      <span className="text-xs font-black text-text-primary truncate">
                        {ppf.name}
                      </span>
                    </div>

                    {/* Current Balance */}
                    <div className="flex flex-col gap-1">
                      <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider">
                        Current Balance
                      </span>
                      <span className="text-xl font-black text-text-primary font-mono">
                        ₹{balanceVal.toLocaleString('en-IN')}
                      </span>
                    </div>

                    {/* Annual Contribution */}
                    <div className="flex flex-col gap-1">
                      <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider">
                        Annual Contribution
                      </span>
                      <span className="text-xs font-black text-text-primary">
                        ₹{annualContributionVal.toLocaleString('en-IN')}
                      </span>
                    </div>

                    {/* Interest & Maturity */}
                    <div className="flex flex-col gap-1">
                      <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider">
                        Interest Rate
                      </span>
                      <div className="flex items-center gap-2">
                        <Badge
                          variant="secondary"
                          className="text-[8px] font-bold py-0.5 px-1.5 bg-success/10 text-success border-success/15 rounded"
                        >
                          {rate.toFixed(2)}% p.a.
                        </Badge>
                        {ppf.maturity_date && (
                          <span className="text-[10px] font-bold text-text-muted">
                            Matures: {ppf.maturity_date}
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-2 justify-end">
                      <button
                        onClick={() => handleEditClick(ppf)}
                        className="p-2 rounded-xl text-text-muted hover:text-primary hover:bg-primary/10 border border-transparent hover:border-primary/10 transition-all duration-200 cursor-pointer"
                        title="Edit PPF"
                      >
                        <LucideIcons.Edit2 className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => setDeleteTargetId(ppf.id)}
                        className="p-2 rounded-xl text-text-muted hover:text-danger hover:bg-danger/10 border border-transparent hover:border-danger/10 transition-all duration-200 cursor-pointer"
                        title="Delete PPF"
                      >
                        <LucideIcons.Trash2 className="h-4 w-4" />
                      </button>
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
              No PPF Account Logged
            </h4>
            <p className="text-xs font-bold text-text-muted/65 mt-1">
              Click the Add PPF button to log a Public Provident Fund account.
            </p>
          </div>
        )}
      </DashboardGrid>

      {/* Add/Edit Modal */}
      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} size="md">
        <form onSubmit={handleFormSubmit}>
          <ModalHeader onClose={() => setIsModalOpen(false)}>
            <span className="text-lg font-black text-text-primary uppercase tracking-wider">
              {editingItem ? 'Edit PPF Account' : 'Add PPF Account'}
            </span>
          </ModalHeader>
          <ModalBody>
            <div className="flex flex-col gap-4 text-left">
              <div className="flex flex-col gap-1.5">
                <label className="text-[10px] font-black text-text-muted uppercase tracking-wider">
                  Account Name / Institution *
                </label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-3 py-2 text-xs font-bold rounded-xl border border-border bg-card text-text-primary focus:outline-none focus:border-primary"
                  placeholder="e.g. Post Office PPF, SBI PPF"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="flex flex-col gap-1.5">
                  <label className="text-[10px] font-black text-text-muted uppercase tracking-wider">
                    Current Account Balance (INR) *
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    required
                    value={balance}
                    onChange={(e) => setBalance(e.target.value)}
                    className="w-full px-3 py-2 text-xs font-bold rounded-xl border border-border bg-card text-text-primary focus:outline-none focus:border-primary"
                    placeholder="e.g. 150000"
                  />
                </div>
                <div className="flex flex-col gap-1.5">
                  <label className="text-[10px] font-black text-text-muted uppercase tracking-wider">
                    Expected Annual Contribution
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={annualContribution}
                    onChange={(e) => setAnnualContribution(e.target.value)}
                    className="w-full px-3 py-2 text-xs font-bold rounded-xl border border-border bg-card text-text-primary focus:outline-none focus:border-primary"
                    placeholder="e.g. 50000"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="flex flex-col gap-1.5">
                  <label className="text-[10px] font-black text-text-muted uppercase tracking-wider">
                    Interest Rate (% p.a.) *
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    required
                    value={interestRate}
                    onChange={(e) => setInterestRate(e.target.value)}
                    className="w-full px-3 py-2 text-xs font-bold rounded-xl border border-border bg-card text-text-primary focus:outline-none focus:border-primary"
                    placeholder="e.g. 7.1"
                  />
                </div>
                <div className="flex flex-col gap-1.5">
                  <label className="text-[10px] font-black text-text-muted uppercase tracking-wider">
                    Maturity Date / Year
                  </label>
                  <input
                    type="date"
                    value={maturityDate}
                    onChange={(e) => setMaturityDate(e.target.value)}
                    className="w-full px-3 py-2 text-xs font-bold rounded-xl border border-border bg-card text-text-primary focus:outline-none focus:border-primary"
                  />
                </div>
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-[10px] font-black text-text-muted uppercase tracking-wider">
                  Notes
                </label>
                <input
                  type="text"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  className="w-full px-3 py-2 text-xs font-bold rounded-xl border border-border bg-card text-text-primary focus:outline-none focus:border-primary"
                  placeholder="Optional details"
                />
              </div>
            </div>
          </ModalBody>
          <ModalFooter>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => setIsModalOpen(false)}
              className="rounded-xl font-bold text-xs"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="gradient"
              size="sm"
              disabled={createMutation.isPending || updateMutation.isPending}
              className="rounded-xl font-bold text-xs"
            >
              {createMutation.isPending || updateMutation.isPending ? 'Saving...' : 'Save PPF'}
            </Button>
          </ModalFooter>
        </form>
      </Modal>

      {/* Delete Confirmation */}
      <ConfirmationDialog
        isOpen={deleteTargetId !== null}
        onClose={() => setDeleteTargetId(null)}
        onConfirm={handleDeleteConfirm}
        title="Delete PPF Account"
        description="Are you sure you want to delete this PPF account entry? Stored contribution history will be permanently lost."
        confirmText={deleteMutation.isPending ? 'Deleting...' : 'Delete PPF'}
        variant="destructive"
      />
    </motion.div>
  )
}

export default PPF
