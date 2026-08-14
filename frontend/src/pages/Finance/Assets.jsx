import React, { useState } from 'react'
import { useProfile, useAssets, useCreateAsset, useDeleteAsset, useUpdateAsset } from '@/hooks'
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

export function Assets() {
  const { profile } = useProfile()
  const shouldReduceMotion = useReducedMotion()

  // Queries & Mutations
  const { data: assetsData, isLoading } = useAssets()
  const createAssetMutation = useCreateAsset()
  const updateAssetMutation = useUpdateAsset()
  const deleteAssetMutation = useDeleteAsset()

  // Modal & Dialog state
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [deleteTargetId, setDeleteTargetId] = useState(null)
  const [editingItem, setEditingItem] = useState(null)

  // Form state
  const [formName, setFormName] = useState('')
  const [formType, setFormType] = useState('BANK_BALANCE')
  const [formValue, setFormValue] = useState('')
  const [formDate, setFormDate] = useState(new Date().toISOString().split('T')[0])
  const [formError, setFormError] = useState(null)

  const assetTypes = [
    { value: 'CASH', label: 'Cash' },
    { value: 'BANK_BALANCE', label: 'Bank Balance' },
    { value: 'PROPERTY', label: 'Real Estate / Property' },
    { value: 'GOLD', label: 'Gold / Precious Metals' },
    { value: 'OTHER', label: 'Other Asset' },
  ]

  const handleAddClick = () => {
    setEditingItem(null)
    setFormName('')
    setFormType('BANK_BALANCE')
    setFormValue('')
    setFormDate(new Date().toISOString().split('T')[0])
    setFormError(null)
    setIsModalOpen(true)
  }

  const handleEditClick = (item) => {
    setEditingItem(item)
    setFormName(item.name)
    setFormType(item.asset_type)
    setFormValue((item.current_value || item.value || 0).toString())
    setFormDate(item.valuation_date)
    setFormError(null)
    setIsModalOpen(true)
  }

  const handleFormSubmit = async (e) => {
    e.preventDefault()
    setFormError(null)

    const val = parseFloat(formValue)
    if (!formName.trim()) {
      setFormError('Asset name is required.')
      return
    }
    if (isNaN(val) || val <= 0) {
      setFormError('Value must be a positive number.')
      return
    }
    if (!formDate) {
      setFormError('Valuation date is required.')
      return
    }

    const payload = {
      name: formName,
      asset_type: formType,
      current_value: val,
      valuation_date: formDate,
    }

    try {
      if (editingItem) {
        await updateAssetMutation.mutateAsync({
          id: editingItem.id,
          data: payload,
        })
      } else {
        await createAssetMutation.mutateAsync(payload)
      }
      setIsModalOpen(false)
    } catch (err) {
      setFormError(err.message || 'Failed to register asset.')
    }
  }

  const handleDeleteConfirm = async () => {
    if (!deleteTargetId) return
    try {
      await deleteAssetMutation.mutateAsync(deleteTargetId)
      setDeleteTargetId(null)
    } catch (err) {
      alert(err.message || 'Failed to delete asset.')
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

  const items = assetsData?.items || []

  // Icon resolver based on asset type
  const getAssetIcon = (type) => {
    switch (type) {
      case 'CASH':
        return LucideIcons.Coins
      case 'BANK_BALANCE':
        return LucideIcons.Wallet
      case 'PROPERTY':
        return LucideIcons.Home
      case 'GOLD':
        return LucideIcons.Gem
      default:
        return LucideIcons.Briefcase
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
            Stored Assets & Equity
          </h3>
          <p className="text-xs font-bold text-text-muted">
            Track property values, checking/savings cash balance, and investment equity.
          </p>
        </div>
        <Button
          variant="gradient"
          size="sm"
          onClick={handleAddClick}
          className="rounded-xl font-bold text-xs gap-1.5 shadow-button"
          iconLeft={<LucideIcons.Plus className="h-4 w-4" />}
        >
          Add Asset
        </Button>
      </div>

      <DashboardGrid>
        {items.length > 0 ? (
          items.map((item, idx) => {
            const Icon = getAssetIcon(item.asset_type)

            return (
              <motion.div
                key={item.id}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: idx * 0.05 }}
                className="lg:col-span-4 md:col-span-1"
              >
                <div className="clay-surface bg-card p-5 border border-white/60 dark:border-white/5 shadow-card flex items-center justify-between gap-4 select-none relative group h-full">
                  {/* Visual bar */}
                  <div className="absolute left-0 top-0 bottom-0 w-1 bg-success transition-all duration-300 group-hover:w-1.5" />

                  <div className="flex flex-col gap-1.5 pl-2 text-left flex-1 min-w-0">
                    <span className="text-[10px] font-black text-text-muted uppercase tracking-wider truncate">
                      {item.name}
                    </span>
                    <span className="text-2xl font-black text-text-primary tracking-tight leading-none truncate">
                      ₹{parseFloat(item.current_value || item.value || 0).toLocaleString('en-IN')}
                    </span>
                    <span className="text-[10px] font-bold text-text-secondary truncate capitalize">
                      {item.asset_type.replace(/_/g, ' ').toLowerCase()}
                    </span>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <button
                      onClick={() => handleEditClick(item)}
                      className="p-2 rounded-xl text-text-muted hover:text-primary hover:bg-primary/10 border border-transparent hover:border-primary/10 transition-all duration-200 cursor-pointer"
                      title="Edit asset"
                    >
                      <LucideIcons.Edit2 className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => setDeleteTargetId(item.id)}
                      className="p-2 rounded-xl text-text-muted hover:text-danger hover:bg-danger/10 border border-transparent hover:border-danger/10 transition-all duration-200 cursor-pointer"
                      title="Remove asset"
                    >
                      <LucideIcons.Trash2 className="h-4 w-4" />
                    </button>
                    <div className="p-3.5 rounded-2xl flex items-center justify-center border border-white/40 dark:border-white/5 bg-success/10 text-success shadow-xs">
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
              No assets configured
            </h4>
            <p className="text-xs font-bold text-text-muted/65 mt-1">
              Add assets like property, cash, bank balance to track net worth.
            </p>
          </div>
        )}

        {/* Premium Asset Allocation Chart Placeholder */}
        <WidgetContainer
          title="Asset Allocation Valuations"
          icon="TrendingUp"
          sizeClass="lg:col-span-12"
        >
          <div className="h-28 w-full rounded-2xl bg-card border border-border/80 relative flex items-end justify-around px-8 pb-3 overflow-hidden mt-2">
            <div className="absolute inset-0 opacity-[0.02] bg-[radial-gradient(#7C3AED_1px,transparent_1px)] [background-size:10px_10px]" />

            <div className="absolute top-2 left-4 flex gap-2">
              <span className="text-[9px] font-black text-text-muted uppercase">
                Liquidity and assets split
              </span>
            </div>

            {/* Horizontal bars mapping */}
            <div className="flex items-center gap-3 w-full px-2">
              <div className="h-4 rounded-full bg-success flex-grow" style={{ width: '55%' }} />
              <div className="h-4 rounded-full bg-primary flex-grow" style={{ width: '30%' }} />
              <div className="h-4 rounded-full bg-accent flex-grow" style={{ width: '15%' }} />
            </div>
          </div>
        </WidgetContainer>
      </DashboardGrid>

      {/* Creation/Edit Modal */}
      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} size="md">
        <form onSubmit={handleFormSubmit} className="flex flex-col h-full">
          <ModalHeader onClose={() => setIsModalOpen(false)}>
            <span className="text-lg font-black text-text-primary uppercase tracking-wider">
              {editingItem ? 'Edit Asset Target' : 'Add Asset Target'}
            </span>
            <span className="text-[10px] font-bold text-text-muted">
              Register cash, banking balances, or gold holdings
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
              <FieldLabel htmlFor="asset-name">Asset Name / Title</FieldLabel>
              <Input
                id="asset-name"
                value={formName}
                onChange={(e) => setFormName(e.target.value)}
                placeholder="e.g. HDFC Savings, Gold Jewelry"
                required
              />
            </div>

            <div className="flex flex-col gap-1.5 text-left">
              <FieldLabel htmlFor="asset-value">Asset Value (₹)</FieldLabel>
              <Input
                id="asset-value"
                type="number"
                value={formValue}
                onChange={(e) => setFormValue(e.target.value)}
                placeholder="e.g. 250000"
                min="1"
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="flex flex-col gap-1.5 text-left">
                <FieldLabel htmlFor="asset-type">Asset Type</FieldLabel>
                <Select
                  id="asset-type"
                  value={formType}
                  onChange={(e) => setFormType(e.target.value)}
                >
                  {assetTypes.map((type) => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </Select>
              </div>

              <div className="flex flex-col gap-1.5 text-left">
                <FieldLabel htmlFor="asset-date">Valuation Date</FieldLabel>
                <Input
                  id="asset-date"
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
              disabled={createAssetMutation.isPending || updateAssetMutation.isPending}
            >
              {editingItem
                ? updateAssetMutation.isPending
                  ? 'Updating...'
                  : 'Update Asset'
                : createAssetMutation.isPending
                  ? 'Saving Asset...'
                  : 'Register Asset'}
            </Button>
          </ModalFooter>
        </form>
      </Modal>

      {/* Confirmation Dialog */}
      <ConfirmationDialog
        isOpen={deleteTargetId !== null}
        onClose={() => setDeleteTargetId(null)}
        onConfirm={handleDeleteConfirm}
        title="Remove Asset?"
        description="Are you sure you want to remove this asset? This will adjust your total net worth immediately."
        confirmText={deleteAssetMutation.isPending ? 'Removing...' : 'Remove Asset'}
        cancelText="Cancel"
        variant="destructive"
      />
    </motion.div>
  )
}

export default Assets
