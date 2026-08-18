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

export function MutualFunds() {
  const { profile } = useProfile()
  const shouldReduceMotion = useReducedMotion()
  const investData = getInvestmentsConfig(profile)

  // Queries and mutations
  const { data: investmentsData, isLoading } = useInvestments({ investment_type: 'MUTUAL_FUND' })
  const createMutation = useCreateInvestment()
  const updateMutation = useUpdateInvestment()
  const deleteMutation = useDeleteInvestment()

  // Modal states
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingItem, setEditingItem] = useState(null)
  const [deleteTargetId, setDeleteTargetId] = useState(null)

  // Form states
  const [name, setName] = useState('')
  const [schemeId, setSchemeId] = useState('')
  const [investedAmount, setInvestedAmount] = useState('')
  const [currentValue, setCurrentValue] = useState('')
  const [units, setUnits] = useState('')
  const [purchaseDate, setPurchaseDate] = useState('')
  const [institution, setInstitution] = useState('')
  const [notes, setNotes] = useState('')

  const handleAddClick = () => {
    setEditingItem(null)
    setName('')
    setSchemeId('')
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
    setSchemeId(item.ticker_symbol || '')
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
      investment_type: 'MUTUAL_FUND',
      invested_amount: parseFloat(investedAmount) || 0,
      current_value: parseFloat(currentValue) || parseFloat(investedAmount) || 0,
      units: units ? parseFloat(units) : null,
      purchase_date: purchaseDate || null,
      ticker_symbol: schemeId || null,
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
      alert(err.message || 'Failed to save mutual fund.')
    }
  }

  const handleDeleteConfirm = async () => {
    if (!deleteTargetId) return
    try {
      await deleteMutation.mutateAsync(deleteTargetId)
      setDeleteTargetId(null)
    } catch (err) {
      alert(err.message || 'Failed to delete mutual fund.')
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

  const mfs = investmentsData?.items || []

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
            Mutual Fund Ledger
          </h3>
          <p className="text-xs font-bold text-text-muted">
            Manage mutual funds portfolios, NAV stats, and annualized return percentages.
          </p>
        </div>
        <Button
          variant="gradient"
          size="sm"
          onClick={handleAddClick}
          className="rounded-xl font-bold text-xs gap-1.5 shadow-button"
          iconLeft={<LucideIcons.Plus className="h-4 w-4" />}
        >
          Add Fund
        </Button>
      </div>

      <DashboardGrid>
        {mfs.length > 0 ? (
          mfs.map((mf, idx) => {
            const invested = parseFloat(mf.invested_amount || 0)
            const current = parseFloat(mf.current_value || 0)
            const profit = current - invested
            const returnsPct = invested > 0 ? (profit / invested) * 100 : 0
            const isUp = profit >= 0

            return (
              <motion.div
                key={mf.id}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: idx * 0.05 }}
                className="lg:col-span-6 md:col-span-1"
              >
                <div className="clay-surface bg-card p-5 border border-white/60 dark:border-white/5 shadow-card flex items-center justify-between gap-4 select-none relative group h-full">
                  <div className="absolute left-0 top-0 bottom-0 w-1 bg-primary transition-all duration-300 group-hover:w-1.5" />

                  <div className="flex flex-col gap-1.5 text-left pl-2 flex-1 min-w-0">
                    <span className="text-xs font-black text-text-primary group-hover:text-primary transition-colors duration-200 truncate">
                      {mf.name}
                    </span>
                    {mf.ticker_symbol && (
                      <span className="text-[10px] font-bold text-text-muted">
                        Scheme ID: {mf.ticker_symbol}
                      </span>
                    )}

                    <div className="flex flex-wrap items-center gap-2 mt-2">
                      <span className="text-lg font-black text-text-primary">
                        NAV: ₹{current.toLocaleString('en-IN')}
                      </span>
                      <Badge
                        variant="secondary"
                        className={`text-[8px] font-bold py-0.5 px-1.5 rounded ${
                          isUp
                            ? 'bg-success/10 text-success border-success/15'
                            : 'bg-danger/10 text-danger border-danger/15'
                        }`}
                      >
                        Returns: {isUp ? '+' : ''}
                        {returnsPct.toFixed(2)}%
                      </Badge>
                    </div>

                    {mf.units && (
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-[10px] font-bold text-text-muted">
                          Units: {parseFloat(mf.units)}
                        </span>
                        {mf.institution && (
                          <Badge
                            variant="secondary"
                            className="text-[8px] font-bold py-0.5 px-1 bg-primary/10 text-primary border-primary/15 rounded"
                          >
                            {mf.institution}
                          </Badge>
                        )}
                      </div>
                    )}
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <button
                      onClick={() => handleEditClick(mf)}
                      className="p-2 rounded-xl text-text-muted hover:text-primary hover:bg-primary/10 border border-transparent hover:border-primary/10 transition-all duration-200 cursor-pointer"
                      title="Edit fund"
                    >
                      <LucideIcons.Edit2 className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => setDeleteTargetId(mf.id)}
                      className="p-2 rounded-xl text-text-muted hover:text-danger hover:bg-danger/10 border border-transparent hover:border-danger/10 transition-all duration-200 cursor-pointer"
                      title="Delete fund"
                    >
                      <LucideIcons.Trash2 className="h-4 w-4" />
                    </button>
                    <div className="p-3.5 rounded-2xl flex items-center justify-center border bg-primary/10 text-primary shadow-xs">
                      <LucideIcons.BarChart2 className="h-5 w-5 stroke-[2px]" />
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
              No Mutual Funds Logged
            </h4>
            <p className="text-xs font-bold text-text-muted/65 mt-1">
              Click the Add Fund button to record mutual fund holdings.
            </p>
          </div>
        )}
      </DashboardGrid>

      {/* Add/Edit Modal */}
      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} size="md">
        <form onSubmit={handleFormSubmit}>
          <ModalHeader onClose={() => setIsModalOpen(false)}>
            <span className="text-lg font-black text-text-primary uppercase tracking-wider">
              {editingItem ? 'Edit Mutual Fund' : 'Add Mutual Fund'}
            </span>
          </ModalHeader>
          <ModalBody>
            <div className="flex flex-col gap-4 text-left">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="flex flex-col gap-1.5">
                  <label className="text-[10px] font-black text-text-muted uppercase tracking-wider">
                    Fund Name *
                  </label>
                  <input
                    type="text"
                    required
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="w-full px-3 py-2 text-xs font-bold rounded-xl border border-border bg-card text-text-primary focus:outline-none focus:border-primary"
                    placeholder="e.g. HDFC Mid-Cap Opportunities"
                  />
                </div>
                <div className="flex flex-col gap-1.5">
                  <label className="text-[10px] font-black text-text-muted uppercase tracking-wider">
                    Scheme ID (AMFI Code)
                  </label>
                  <input
                    type="text"
                    value={schemeId}
                    onChange={(e) => setSchemeId(e.target.value)}
                    className="w-full px-3 py-2 text-xs font-bold rounded-xl border border-border bg-card text-text-primary focus:outline-none focus:border-primary"
                    placeholder="e.g. 119063"
                  />
                </div>
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
                    placeholder="e.g. 100000"
                  />
                </div>
                <div className="flex flex-col gap-1.5">
                  <label className="text-[10px] font-black text-text-muted uppercase tracking-wider">
                    Current NAV Value (INR)
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
                    Units Held
                  </label>
                  <input
                    type="number"
                    step="0.000001"
                    min="0"
                    value={units}
                    onChange={(e) => setUnits(e.target.value)}
                    className="w-full px-3 py-2 text-xs font-bold rounded-xl border border-border bg-card text-text-primary focus:outline-none focus:border-primary"
                    placeholder="e.g. 686.81"
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
                    AMC / Institution
                  </label>
                  <input
                    type="text"
                    value={institution}
                    onChange={(e) => setInstitution(e.target.value)}
                    className="w-full px-3 py-2 text-xs font-bold rounded-xl border border-border bg-card text-text-primary focus:outline-none focus:border-primary"
                    placeholder="e.g. HDFC Mutual Fund"
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
              {createMutation.isPending || updateMutation.isPending ? 'Saving...' : 'Save Fund'}
            </Button>
          </ModalFooter>
        </form>
      </Modal>

      {/* Delete Confirmation */}
      <ConfirmationDialog
        isOpen={deleteTargetId !== null}
        onClose={() => setDeleteTargetId(null)}
        onConfirm={handleDeleteConfirm}
        title="Delete Mutual Fund Holding"
        description="Are you sure you want to delete this mutual fund record? All historical valuation logs will be permanently removed."
        confirmText={deleteMutation.isPending ? 'Deleting...' : 'Delete Fund'}
        variant="destructive"
      />
    </motion.div>
  )
}

export default MutualFunds
