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

export function Gold() {
  const { profile } = useProfile()
  const shouldReduceMotion = useReducedMotion()
  const investData = getInvestmentsConfig(profile)

  // Queries and mutations
  const { data: investmentsData, isLoading } = useInvestments({ investment_type: 'GOLD' })
  const createMutation = useCreateInvestment()
  const updateMutation = useUpdateInvestment()
  const deleteMutation = useDeleteInvestment()

  // Modal states
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingItem, setEditingItem] = useState(null)
  const [deleteTargetId, setDeleteTargetId] = useState(null)

  // Form states
  const [name, setName] = useState('')
  const [investedAmount, setInvestedAmount] = useState('')
  const [currentValue, setCurrentValue] = useState('')
  const [units, setUnits] = useState('')
  const [purchaseDate, setPurchaseDate] = useState('')
  const [institution, setInstitution] = useState('')
  const [notes, setNotes] = useState('')

  const handleAddClick = () => {
    setEditingItem(null)
    setName('')
    setInvestedAmount('')
    setCurrentValue('')
    setUnits('')
    setPurchaseDate(new Date().toISOString().split('T')[0])
    setInstitution('')
    setNotes('')
    setIsModalOpen(true)
  }

  const handleEditClick = (item) => {
    setEditingItem(item)
    setName(item.name || '')
    setInvestedAmount(item.invested_amount || '')
    setCurrentValue(item.current_value || '')
    setUnits(item.units || '')
    setPurchaseDate(item.purchase_date || new Date().toISOString().split('T')[0])
    setInstitution(item.institution || '')
    setNotes(item.notes || '')
    setIsModalOpen(true)
  }

  const handleFormSubmit = async (e) => {
    e.preventDefault()
    const payload = {
      name,
      investment_type: 'GOLD',
      invested_amount: parseFloat(investedAmount) || 0,
      current_value: parseFloat(currentValue) || parseFloat(investedAmount) || 0,
      units: units ? parseFloat(units) : null,
      purchase_date: purchaseDate || null,
      institution: institution || null,
      notes: notes || null,
    }

    try {
      if (editingItem) {
        await updateMutation.mutateAsync({ id: editingItem.id, data: payload })
      } else {
        await createMutation.mutateAsync(payload)
      }
      setIsModalOpen(false)
    } catch (err) {
      alert(err.message || 'Failed to save Gold holding.')
    }
  }

  const handleDeleteConfirm = async () => {
    if (!deleteTargetId) return
    try {
      await deleteMutation.mutateAsync(deleteTargetId)
      setDeleteTargetId(null)
    } catch (err) {
      alert(err.message || 'Failed to delete Gold holding.')
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

  const golds = investmentsData?.items || []

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
            Precious Gold Bullions
          </h3>
          <p className="text-xs font-bold text-text-muted">
            Track digital and physical sovereign gold coins, gram quantities, and growth yields.
          </p>
        </div>
        <Button
          variant="gradient"
          size="sm"
          onClick={handleAddClick}
          className="rounded-xl font-bold text-xs gap-1.5 shadow-button"
          iconLeft={<LucideIcons.Plus className="h-4 w-4" />}
        >
          Add Gold
        </Button>
      </div>

      <DashboardGrid>
        {golds.length > 0 ? (
          golds.map((g, idx) => {
            const invested = parseFloat(g.invested_amount || 0)
            const current = parseFloat(g.current_value || 0)
            const profit = current - invested
            const returnsPct = invested > 0 ? (profit / invested) * 100 : 0
            const isUp = profit >= 0

            return (
              <motion.div
                key={g.id}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: idx * 0.05 }}
                className="lg:col-span-6 md:col-span-1"
              >
                <div className="clay-surface bg-card p-5 border border-white/60 dark:border-white/5 shadow-card flex items-center justify-between gap-4 select-none relative group h-full">
                  <div className="absolute left-0 top-0 bottom-0 w-1 bg-primary transition-all duration-300 group-hover:w-1.5" />

                  <div className="flex flex-col gap-1.5 text-left pl-2 flex-1 min-w-0">
                    <span className="text-xs font-black text-text-primary group-hover:text-primary transition-colors duration-200 truncate">
                      {g.name}
                    </span>
                    <span className="text-lg font-black text-text-primary mt-1 font-mono">
                      Valuation: ₹{current.toLocaleString('en-IN')}
                    </span>

                    <div className="flex items-center gap-2 mt-2">
                      <Badge
                        variant="secondary"
                        className={`text-[8px] font-bold py-0.5 px-1.5 rounded ${isUp ? 'bg-success/10 text-success' : 'bg-danger/10 text-danger'}`}
                      >
                        Growth: {isUp ? '+' : ''}
                        {returnsPct.toFixed(2)}%
                      </Badge>
                      {g.units && (
                        <span className="text-[10px] font-bold text-text-muted">
                          Qty: {parseFloat(g.units)} Grams
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <button
                      onClick={() => handleEditClick(g)}
                      className="p-2 rounded-xl text-text-muted hover:text-primary hover:bg-primary/10 border border-transparent hover:border-primary/10 transition-all duration-200 cursor-pointer"
                      title="Edit gold"
                    >
                      <LucideIcons.Edit2 className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => setDeleteTargetId(g.id)}
                      className="p-2 rounded-xl text-text-muted hover:text-danger hover:bg-danger/10 border border-transparent hover:border-danger/10 transition-all duration-200 cursor-pointer"
                      title="Delete gold"
                    >
                      <LucideIcons.Trash2 className="h-4 w-4" />
                    </button>
                    <div className="p-3.5 rounded-2xl flex items-center justify-center border bg-warning/10 text-warning shadow-xs shrink-0">
                      <LucideIcons.Gem className="h-5 w-5 stroke-[2px]" />
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
              No Gold Asset Holdings
            </h4>
            <p className="text-xs font-bold text-text-muted/65 mt-1">
              Click the Add Gold button to record sovereign or bullion gold holdings.
            </p>
          </div>
        )}
      </DashboardGrid>

      {/* Add/Edit Modal */}
      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} size="md">
        <form onSubmit={handleFormSubmit}>
          <ModalHeader onClose={() => setIsModalOpen(false)}>
            <span className="text-lg font-black text-text-primary uppercase tracking-wider">
              {editingItem ? 'Edit Gold Holding' : 'Add Gold Holding'}
            </span>
          </ModalHeader>
          <ModalBody>
            <div className="flex flex-col gap-4 text-left">
              <div className="flex flex-col gap-1.5">
                <label className="text-[10px] font-black text-text-muted uppercase tracking-wider">
                  Gold Description *
                </label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-3 py-2 text-xs font-bold rounded-xl border border-border bg-card text-text-primary focus:outline-none focus:border-primary"
                  placeholder="e.g. Sovereign Gold Bonds, 24K Physical Gold"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="flex flex-col gap-1.5">
                  <label className="text-[10px] font-black text-text-muted uppercase tracking-wider">
                    Invested Amount (INR) *
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    required
                    value={investedAmount}
                    onChange={(e) => setInvestedAmount(e.target.value)}
                    className="w-full px-3 py-2 text-xs font-bold rounded-xl border border-border bg-card text-text-primary focus:outline-none focus:border-primary"
                    placeholder="e.g. 20000"
                  />
                </div>
                <div className="flex flex-col gap-1.5">
                  <label className="text-[10px] font-black text-text-muted uppercase tracking-wider">
                    Current Market Value (INR)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={currentValue}
                    onChange={(e) => setCurrentValue(e.target.value)}
                    className="w-full px-3 py-2 text-xs font-bold rounded-xl border border-border bg-card text-text-primary focus:outline-none focus:border-primary"
                    placeholder="Defaults to invested amount"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="flex flex-col gap-1.5">
                  <label className="text-[10px] font-black text-text-muted uppercase tracking-wider">
                    Quantity (Grams) *
                  </label>
                  <input
                    type="number"
                    step="0.0001"
                    min="0"
                    required
                    value={units}
                    onChange={(e) => setUnits(e.target.value)}
                    className="w-full px-3 py-2 text-xs font-bold rounded-xl border border-border bg-card text-text-primary focus:outline-none focus:border-primary"
                    placeholder="e.g. 5.5"
                  />
                </div>
                <div className="flex flex-col gap-1.5">
                  <label className="text-[10px] font-black text-text-muted uppercase tracking-wider">
                    Purchase Date
                  </label>
                  <input
                    type="date"
                    value={purchaseDate}
                    onChange={(e) => setPurchaseDate(e.target.value)}
                    className="w-full px-3 py-2 text-xs font-bold rounded-xl border border-border bg-card text-text-primary focus:outline-none focus:border-primary"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="flex flex-col gap-1.5">
                  <label className="text-[10px] font-black text-text-muted uppercase tracking-wider">
                    Custodian / Institution
                  </label>
                  <input
                    type="text"
                    value={institution}
                    onChange={(e) => setInstitution(e.target.value)}
                    className="w-full px-3 py-2 text-xs font-bold rounded-xl border border-border bg-card text-text-primary focus:outline-none focus:border-primary"
                    placeholder="e.g. RBI, MMTC-PAMP"
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
              {createMutation.isPending || updateMutation.isPending ? 'Saving...' : 'Save Gold'}
            </Button>
          </ModalFooter>
        </form>
      </Modal>

      {/* Delete Confirmation */}
      <ConfirmationDialog
        isOpen={deleteTargetId !== null}
        onClose={() => setDeleteTargetId(null)}
        onConfirm={handleDeleteConfirm}
        title="Delete Gold Holding"
        description="Are you sure you want to delete this gold holding record? This action cannot be undone."
        confirmText={deleteMutation.isPending ? 'Deleting...' : 'Delete Gold'}
        variant="destructive"
      />
    </motion.div>
  )
}

export default Gold
