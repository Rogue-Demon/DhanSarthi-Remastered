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

export function NPS() {
  const { profile } = useProfile()
  const shouldReduceMotion = useReducedMotion()
  const investData = getInvestmentsConfig(profile)

  // Queries and mutations (fetch OTHER types and filter for NPS subtype client-side)
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
  const [corpus, setCorpus] = useState('')
  const [monthlyContribution, setMonthlyContribution] = useState('')
  const [tier, setTier] = useState('Tier I')
  const [allocation, setAllocation] = useState('')
  const [projection, setProjection] = useState('')
  const [notes, setNotes] = useState('')

  const handleAddClick = () => {
    setEditingItem(null)
    setName('')
    setCorpus('')
    setMonthlyContribution('')
    setTier('Tier I')
    setAllocation('Equity 75%, Corporate Debt 15%, Govt Bonds 10%')
    setProjection('Estimated ₹1.5 Crore at age 60')
    setNotes('')
    setIsModalOpen(true)
  }

  const handleEditClick = (item) => {
    setEditingItem(item)
    setName(item.name || '')
    setCorpus(item.current_value || '')
    setMonthlyContribution(item.invested_amount || '')
    setTier(item.investment_metadata?.tier || 'Tier I')
    setAllocation(item.investment_metadata?.allocation || '')
    setProjection(item.investment_metadata?.projection || '')
    setNotes(item.notes || '')
    setIsModalOpen(true)
  }

  const handleFormSubmit = async (e) => {
    e.preventDefault()
    const payload = {
      name,
      investment_type: 'OTHER',
      invested_amount: parseFloat(monthlyContribution) || 0,
      current_value: parseFloat(corpus) || 0,
      notes: notes || null,
      investment_metadata: {
        subtype: 'NPS',
        tier,
        allocation,
        projection,
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
      alert(err.message || 'Failed to save NPS account.')
    }
  }

  const handleDeleteConfirm = async () => {
    if (!deleteTargetId) return
    try {
      await deleteMutation.mutateAsync(deleteTargetId)
      setDeleteTargetId(null)
    } catch (err) {
      alert(err.message || 'Failed to delete NPS account.')
    }
  }

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 gap-6 w-full animate-pulse">
        <div className="h-28 bg-muted/20 rounded-2xl border" />
      </div>
    )
  }

  const npsList = (investmentsData?.items || []).filter(
    (item) => item.investment_metadata?.subtype === 'NPS'
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
            National Pension System (NPS)
          </h3>
          <p className="text-xs font-bold text-text-muted">
            Government-backed retirement savings with equity, corporate debt, and government bond
            allocations.
          </p>
        </div>
        <Button
          variant="gradient"
          size="sm"
          onClick={handleAddClick}
          className="rounded-xl font-bold text-xs gap-1.5 shadow-button"
          iconLeft={<LucideIcons.Plus className="h-4 w-4" />}
        >
          Add NPS Account
        </Button>
      </div>

      <DashboardGrid>
        {npsList.length > 0 ? (
          npsList.map((nps, idx) => {
            const corpusVal = parseFloat(nps.current_value || 0)
            const monthlyVal = parseFloat(nps.invested_amount || 0)
            const tierVal = nps.investment_metadata?.tier || 'Tier I'
            const allocationVal = nps.investment_metadata?.allocation || 'Active Choice'
            const projectionVal = nps.investment_metadata?.projection || 'N/A'

            return (
              <motion.div
                key={nps.id}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: idx * 0.05 }}
                className="lg:col-span-12 md:col-span-2"
              >
                <div className="clay-surface bg-card p-6 border border-white/60 dark:border-white/5 shadow-card select-none relative group">
                  <div className="absolute left-0 top-0 bottom-0 w-1 bg-primary transition-all duration-300 group-hover:w-1.5" />

                  <div className="grid grid-cols-1 sm:grid-cols-4 gap-6 pl-2 text-left items-center">
                    {/* Current Corpus */}
                    <div className="flex flex-col gap-1">
                      <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider">
                        Current Corpus
                      </span>
                      <span className="text-2xl font-black text-text-primary tracking-tight font-mono">
                        ₹{corpusVal.toLocaleString('en-IN')}
                      </span>
                      <span className="text-[10px] font-bold text-text-muted mt-0.5">
                        Monthly: ₹{monthlyVal.toLocaleString('en-IN')}
                      </span>
                    </div>

                    {/* Tier & Fund Allocation */}
                    <div className="flex flex-col gap-1">
                      <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider">
                        Tier & Allocation
                      </span>
                      <Badge
                        variant="secondary"
                        className="mr-auto text-[9px] font-bold py-0.5 px-2 bg-primary/10 text-primary border-primary/15 rounded mt-1"
                      >
                        {tierVal}
                      </Badge>
                      <span className="text-[10px] font-bold text-text-secondary mt-1.5 leading-relaxed truncate">
                        {allocationVal}
                      </span>
                    </div>

                    {/* Retirement Projection */}
                    <div className="flex flex-col gap-1">
                      <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider">
                        Retirement Projection
                      </span>
                      <div className="flex items-start gap-2 mt-1">
                        <div className="h-5 w-5 rounded-full bg-success/10 flex items-center justify-center shrink-0 text-success mt-0.5">
                          <LucideIcons.Sparkles className="h-3 w-3" />
                        </div>
                        <p className="text-xs font-semibold text-text-secondary leading-relaxed">
                          {projectionVal}
                        </p>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-2 justify-end">
                      <button
                        onClick={() => handleEditClick(nps)}
                        className="p-2 rounded-xl text-text-muted hover:text-primary hover:bg-primary/10 border border-transparent hover:border-primary/10 transition-all duration-200 cursor-pointer"
                        title="Edit NPS"
                      >
                        <LucideIcons.Edit2 className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => setDeleteTargetId(nps.id)}
                        className="p-2 rounded-xl text-text-muted hover:text-danger hover:bg-danger/10 border border-transparent hover:border-danger/10 transition-all duration-200 cursor-pointer"
                        title="Delete NPS"
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
              No NPS Account Active
            </h4>
            <p className="text-xs font-bold text-text-muted/65 mt-1">
              Click the Add NPS Account button to record retirement accounts.
            </p>
          </div>
        )}

        {/* NPS Growth Chart Projection */}
        {npsList.length > 0 && (
          <WidgetContainer
            title="NPS Corpus Growth Projection"
            icon="TrendingUp"
            sizeClass="lg:col-span-12"
          >
            <div className="h-32 w-full rounded-2xl bg-card border border-border/80 relative flex items-end justify-between px-8 pb-3 overflow-hidden mt-2">
              <div className="absolute inset-0 opacity-[0.02] bg-[radial-gradient(#7C3AED_1px,transparent_1px)] [background-size:12px_12px]" />

              {/* Visual graph path */}
              <svg
                className="absolute inset-0 w-full h-full text-primary/10"
                preserveAspectRatio="none"
                viewBox="0 0 100 100"
              >
                <path d="M0,95 Q15,90 30,80 T60,50 T90,20 T100,10 L100,100 Z" fill="currentColor" />
                <path
                  d="M0,95 Q15,90 30,80 T60,50 T90,20 T100,10"
                  fill="none"
                  stroke="var(--primary)"
                  strokeWidth="2"
                />
              </svg>

              {['2026', '2030', '2035', '2040', '2050'].map((yr) => (
                <span key={yr} className="text-[9px] font-black text-text-muted z-10">
                  {yr}
                </span>
              ))}

              <div className="absolute top-3 right-4 flex items-center gap-1.5 text-[10px] font-bold text-text-muted">
                <LucideIcons.Sparkles className="h-3.5 w-3.5 text-accent animate-pulse" />
                <span>Projected growth trajectory</span>
              </div>
            </div>
          </WidgetContainer>
        )}
      </DashboardGrid>

      {/* Add/Edit Modal */}
      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} size="md">
        <form onSubmit={handleFormSubmit}>
          <ModalHeader onClose={() => setIsModalOpen(false)}>
            <span className="text-lg font-black text-text-primary uppercase tracking-wider">
              {editingItem ? 'Edit NPS Account' : 'Add NPS Account'}
            </span>
          </ModalHeader>
          <ModalBody>
            <div className="flex flex-col gap-4 text-left">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="flex flex-col gap-1.5">
                  <label className="text-[10px] font-black text-text-muted uppercase tracking-wider">
                    Account Title / Scheme Name *
                  </label>
                  <input
                    type="text"
                    required
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="w-full px-3 py-2 text-xs font-bold rounded-xl border border-border bg-card text-text-primary focus:outline-none focus:border-primary"
                    placeholder="e.g. My Pension Fund"
                  />
                </div>
                <div className="flex flex-col gap-1.5">
                  <label className="text-[10px] font-black text-text-muted uppercase tracking-wider">
                    Tier Choice
                  </label>
                  <select
                    value={tier}
                    onChange={(e) => setTier(e.target.value)}
                    className="w-full px-3 py-2 text-xs font-bold rounded-xl border border-border bg-card text-text-primary focus:outline-none focus:border-primary"
                  >
                    <option value="Tier I">Tier I (Retirement)</option>
                    <option value="Tier II">Tier II (Savings)</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="flex flex-col gap-1.5">
                  <label className="text-[10px] font-black text-text-muted uppercase tracking-wider">
                    Current Corpus (INR) *
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    required
                    value={corpus}
                    onChange={(e) => setCorpus(e.target.value)}
                    className="w-full px-3 py-2 text-xs font-bold rounded-xl border border-border bg-card text-text-primary focus:outline-none focus:border-primary"
                    placeholder="e.g. 350000"
                  />
                </div>
                <div className="flex flex-col gap-1.5">
                  <label className="text-[10px] font-black text-text-muted uppercase tracking-wider">
                    Monthly Contribution (INR)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={monthlyContribution}
                    onChange={(e) => setMonthlyContribution(e.target.value)}
                    className="w-full px-3 py-2 text-xs font-bold rounded-xl border border-border bg-card text-text-primary focus:outline-none focus:border-primary"
                    placeholder="e.g. 5000"
                  />
                </div>
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-[10px] font-black text-text-muted uppercase tracking-wider">
                  Asset Allocation Details
                </label>
                <input
                  type="text"
                  value={allocation}
                  onChange={(e) => setAllocation(e.target.value)}
                  className="w-full px-3 py-2 text-xs font-bold rounded-xl border border-border bg-card text-text-primary focus:outline-none focus:border-primary"
                  placeholder="e.g. Equity 75%, Corporate Debt 15%, Govt Bonds 10%"
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-[10px] font-black text-text-muted uppercase tracking-wider">
                  Retirement Projection Statement
                </label>
                <input
                  type="text"
                  value={projection}
                  onChange={(e) => setProjection(e.target.value)}
                  className="w-full px-3 py-2 text-xs font-bold rounded-xl border border-border bg-card text-text-primary focus:outline-none focus:border-primary"
                  placeholder="e.g. Estimated ₹1.5 Crore at age 60"
                />
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
              {createMutation.isPending || updateMutation.isPending ? 'Saving...' : 'Save NPS'}
            </Button>
          </ModalFooter>
        </form>
      </Modal>

      {/* Delete Confirmation */}
      <ConfirmationDialog
        isOpen={deleteTargetId !== null}
        onClose={() => setDeleteTargetId(null)}
        onConfirm={handleDeleteConfirm}
        title="Delete NPS Account"
        description="Are you sure you want to delete this NPS account? Stored values and contribution history will be permanently deleted."
        confirmText={deleteMutation.isPending ? 'Deleting...' : 'Delete NPS'}
        variant="destructive"
      />
    </motion.div>
  )
}

export default NPS
