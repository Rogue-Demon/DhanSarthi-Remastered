import { useState, useRef } from 'react'
import { motion, useReducedMotion } from 'framer-motion'
import { Badge, Button } from '@/components/ui'
import { Modal, ModalHeader, ModalBody, ModalFooter } from '@/components/overlay'
import * as LucideIcons from 'lucide-react'
import {
  useDocuments,
  useUploadDocument,
  useProcessDocument,
  useDocumentExtraction,
  useConfirmDocument,
  useDeleteDocument,
} from '@/hooks/useDocuments'
import { cn } from '@/utils'

// Helper to format file size
function formatBytes(bytes) {
  if (!bytes || bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`
}

// Format document type for human display
function formatDocType(type) {
  const map = {
    BANK_STATEMENT: 'Bank Statement',
    SALARY_SLIP: 'Salary Slip',
    LOAN_STATEMENT: 'Loan Statement',
    INVESTMENT_STATEMENT: 'Investment Statement',
    TAX_DOCUMENT: 'Tax Document',
    BILL: 'Utility / Invoice Bill',
    UNKNOWN: 'Unclassified Document',
  }
  return map[type] || type
}

// Icon for document type
function getDocTypeIcon(type) {
  switch (type) {
    case 'BANK_STATEMENT':
      return LucideIcons.Landmark
    case 'SALARY_SLIP':
      return LucideIcons.BadgeDollarSign
    case 'LOAN_STATEMENT':
      return LucideIcons.HandCoins
    case 'INVESTMENT_STATEMENT':
      return LucideIcons.TrendingUp
    case 'TAX_DOCUMENT':
      return LucideIcons.ReceiptText
    case 'BILL':
      return LucideIcons.FileSpreadsheet
    default:
      return LucideIcons.FileText
  }
}

// Status badge styling helper
function getStatusBadge(status) {
  switch (status) {
    case 'CONFIRMED':
      return {
        label: 'Confirmed & Imported',
        variant: 'success',
        color: 'bg-emerald-500/10 text-emerald-600 border-emerald-500/20',
      }
    case 'REVIEW_REQUIRED':
      return {
        label: 'Review Required',
        variant: 'warning',
        color: 'bg-amber-500/10 text-amber-600 border-amber-500/20',
      }
    case 'EXTRACTED':
      return {
        label: 'Extracted',
        variant: 'info',
        color: 'bg-sky-500/10 text-sky-600 border-sky-500/20',
      }
    case 'PROCESSING':
      return {
        label: 'Processing...',
        variant: 'default',
        color: 'bg-indigo-500/10 text-indigo-600 border-indigo-500/20 animate-pulse',
      }
    case 'FAILED':
      return {
        label: 'Processing Failed',
        variant: 'danger',
        color: 'bg-rose-500/10 text-rose-600 border-rose-500/20',
      }
    case 'UPLOADED':
    default:
      return {
        label: 'Uploaded',
        variant: 'secondary',
        color: 'bg-primary/10 text-primary border-primary/20',
      }
  }
}

export function Documents() {
  const shouldReduceMotion = useReducedMotion()
  const fileInputRef = useRef(null)

  const [dragActive, setDragActive] = useState(false)
  const [uploadError, setUploadError] = useState(null)
  const [reviewDocId, setReviewDocId] = useState(null)
  const [deselectedFields, setDeselectedFields] = useState([])
  const [deselectedTxs, setDeselectedTxs] = useState([])
  const [deselectedIncomeIds, setDeselectedIncomeIds] = useState([])
  const [deselectedExpenseIds, setDeselectedExpenseIds] = useState([])
  const [deselectedAssetIds, setDeselectedAssetIds] = useState([])
  const [deselectedLiabilityIds, setDeselectedLiabilityIds] = useState([])
  const [confirmationSuccess, setConfirmationSuccess] = useState(null)

  // Queries & mutations
  const { data: docListData, isLoading, isError } = useDocuments()
  const documents = docListData?.items ?? []

  const uploadMutation = useUploadDocument()
  const processMutation = useProcessDocument()
  const deleteMutation = useDeleteDocument()
  const confirmMutation = useConfirmDocument()

  // Extraction query for the currently reviewed document
  const { data: extractionData, isLoading: isLoadingExtraction } = useDocumentExtraction(
    reviewDocId,
    {
      enabled: Boolean(reviewDocId),
    }
  )

  // Calculate summary stats
  const totalCount = documents.length
  const reviewCount = documents.filter(
    (d) => d.status === 'REVIEW_REQUIRED' || d.status === 'EXTRACTED'
  ).length
  const confirmedCount = documents.filter((d) => d.status === 'CONFIRMED').length
  const failedCount = documents.filter((d) => d.status === 'FAILED').length

  // Derived confirmed fields, transactions, and candidates
  const allFieldNames = (extractionData?.fields || []).map((f) => f.name)
  const allTxIds = (extractionData?.transactions || []).map((t) => t.candidate_id)

  const confirmedFieldNames = allFieldNames.filter((name) => !deselectedFields.includes(name))
  const confirmedTxIds = allTxIds.filter((id) => !deselectedTxs.includes(id))
  const confirmedIncomes = (extractionData?.income_candidates || []).filter(
    (c) => !deselectedIncomeIds.includes(c.candidate_id)
  )
  const confirmedExpenses = (extractionData?.expense_candidates || []).filter(
    (c) => !deselectedExpenseIds.includes(c.candidate_id)
  )
  const confirmedAssets = (extractionData?.asset_candidates || []).filter(
    (c) => !deselectedAssetIds.includes(c.candidate_id)
  )
  const confirmedLiabilities = (extractionData?.liability_candidates || []).filter(
    (c) => !deselectedLiabilityIds.includes(c.candidate_id)
  )

  const totalSelectedCount =
    confirmedFieldNames.length +
    confirmedTxIds.length +
    confirmedIncomes.length +
    confirmedExpenses.length +
    confirmedAssets.length +
    confirmedLiabilities.length

  // ── Drag & Drop Handlers ──────────────────────────────────────────────────
  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const validateAndUpload = (file) => {
    setUploadError(null)
    if (!file) return

    // Size check (10MB)
    const maxBytes = 10 * 1024 * 1024
    if (file.size > maxBytes) {
      setUploadError(
        `File is too large (${formatBytes(file.size)}). Maximum allowed size is 10 MB.`
      )
      return
    }

    // Supported format check
    const allowedExtensions = ['pdf', 'csv', 'png', 'jpg', 'jpeg', 'txt']
    const ext = file.name.split('.').pop().toLowerCase()
    if (!allowedExtensions.includes(ext)) {
      setUploadError(
        `Unsupported file format (.${ext}). Supported formats: PDF, CSV, PNG, JPG, TXT.`
      )
      return
    }

    uploadMutation.mutate(file, {
      onError: (err) => {
        setUploadError(err.response?.data?.detail || err.message || 'Failed to upload document.')
      },
    })
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndUpload(e.dataTransfer.files[0])
    }
  }

  const handleFileInputChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      validateAndUpload(e.target.files[0])
      e.target.value = ''
    }
  }

  // ── Review Modal Handlers ─────────────────────────────────────────────────
  const handleOpenReview = (doc) => {
    setReviewDocId(doc.id)
    setDeselectedFields([])
    setDeselectedTxs([])
    setDeselectedIncomeIds([])
    setDeselectedExpenseIds([])
    setDeselectedAssetIds([])
    setDeselectedLiabilityIds([])
    setConfirmationSuccess(null)
  }

  const handleToggleField = (fieldName) => {
    setDeselectedFields((prev) =>
      prev.includes(fieldName) ? prev.filter((name) => name !== fieldName) : [...prev, fieldName]
    )
  }

  const handleToggleTx = (txId) => {
    setDeselectedTxs((prev) =>
      prev.includes(txId) ? prev.filter((id) => id !== txId) : [...prev, txId]
    )
  }

  const handleSelectAllTxs = (select) => {
    if (!extractionData) return
    if (select) {
      setDeselectedTxs([])
    } else {
      setDeselectedTxs(allTxIds)
    }
  }

  const handleConfirmImport = () => {
    if (!reviewDocId) return

    confirmMutation.mutate(
      {
        documentId: reviewDocId,
        data: {
          confirmed_fields: confirmedFieldNames,
          confirmed_transactions: confirmedTxIds,
          confirmed_income: confirmedIncomes,
          confirmed_expenses: confirmedExpenses,
          confirmed_assets: confirmedAssets,
          confirmed_liabilities: confirmedLiabilities,
        },
      },
      {
        onSuccess: (res) => {
          setConfirmationSuccess(res)
        },
      }
    )
  }

  const handleDelete = (docId, filename) => {
    if (!window.confirm(`Delete document "${filename}"? This will remove the file from storage.`))
      return
    deleteMutation.mutate(docId)
  }

  const handleProcess = (docId) => {
    processMutation.mutate(docId, {
      onSuccess: () => {
        setReviewDocId(docId)
      },
    })
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: shouldReduceMotion ? 0 : 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="flex flex-col gap-6 p-4 md:p-6 w-full max-w-7xl mx-auto select-none text-left"
    >
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2">
            <h2 className="text-xl md:text-2xl font-black text-text-primary uppercase tracking-tight">
              Document Intelligence
            </h2>
            <Badge
              variant="secondary"
              className="text-[10px] font-black uppercase tracking-widest bg-primary/10 text-primary border-primary/20 py-0.5 px-2.5"
            >
              Secure Extraction
            </Badge>
          </div>
          <p className="text-xs font-bold text-text-muted">
            Upload financial statements, salary slips, and bills to extract structured records with
            human review.
          </p>
        </div>

        <Button
          variant="primary"
          size="sm"
          onClick={() => fileInputRef.current?.click()}
          iconLeft={<LucideIcons.Upload className="h-4 w-4" />}
          className="font-black uppercase tracking-wider text-xs shrink-0"
        >
          Upload Document
        </Button>
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileInputChange}
          accept=".pdf,.csv,.png,.jpg,.jpeg,.txt"
          className="hidden"
        />
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="clay-surface bg-card p-4 rounded-2xl border border-white/60 dark:border-white/5 shadow-card flex items-center justify-between">
          <div className="flex flex-col gap-0.5">
            <span className="text-[10px] font-black text-text-muted uppercase tracking-wider">
              Total Documents
            </span>
            <span className="text-xl font-black text-text-primary">{totalCount}</span>
          </div>
          <div className="p-3 rounded-2xl bg-primary/10 text-primary">
            <LucideIcons.Files className="h-5 w-5" />
          </div>
        </div>

        <div className="clay-surface bg-card p-4 rounded-2xl border border-white/60 dark:border-white/5 shadow-card flex items-center justify-between">
          <div className="flex flex-col gap-0.5">
            <span className="text-[10px] font-black text-text-muted uppercase tracking-wider">
              Ready for Review
            </span>
            <span className="text-xl font-black text-amber-500">{reviewCount}</span>
          </div>
          <div className="p-3 rounded-2xl bg-amber-500/10 text-amber-500">
            <LucideIcons.Eye className="h-5 w-5" />
          </div>
        </div>

        <div className="clay-surface bg-card p-4 rounded-2xl border border-white/60 dark:border-white/5 shadow-card flex items-center justify-between">
          <div className="flex flex-col gap-0.5">
            <span className="text-[10px] font-black text-text-muted uppercase tracking-wider">
              Confirmed / Imported
            </span>
            <span className="text-xl font-black text-emerald-500">{confirmedCount}</span>
          </div>
          <div className="p-3 rounded-2xl bg-emerald-500/10 text-emerald-500">
            <LucideIcons.CheckCircle2 className="h-5 w-5" />
          </div>
        </div>

        <div className="clay-surface bg-card p-4 rounded-2xl border border-white/60 dark:border-white/5 shadow-card flex items-center justify-between">
          <div className="flex flex-col gap-0.5">
            <span className="text-[10px] font-black text-text-muted uppercase tracking-wider">
              Failed Extraction
            </span>
            <span className="text-xl font-black text-rose-500">{failedCount}</span>
          </div>
          <div className="p-3 rounded-2xl bg-rose-500/10 text-rose-500">
            <LucideIcons.AlertTriangle className="h-5 w-5" />
          </div>
        </div>
      </div>

      {/* Upload Dropzone */}
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={cn(
          'clay-surface bg-card p-8 border-2 border-dashed rounded-3xl shadow-card transition-all cursor-pointer text-center flex flex-col items-center justify-center gap-3',
          dragActive
            ? 'border-primary bg-primary/5 scale-[0.99]'
            : 'border-border hover:border-primary/40'
        )}
      >
        <div className="h-14 w-14 rounded-2xl bg-primary/10 text-primary flex items-center justify-center shadow-xs">
          {uploadMutation.isPending ? (
            <LucideIcons.Loader2 className="h-7 w-7 animate-spin" />
          ) : (
            <LucideIcons.CloudUpload className="h-7 w-7" />
          )}
        </div>

        <div className="flex flex-col gap-1 max-w-md">
          <h4 className="text-sm font-black text-text-primary uppercase tracking-wider">
            {uploadMutation.isPending ? 'Uploading Document...' : 'Drag & Drop Financial Document'}
          </h4>
          <p className="text-xs font-bold text-text-muted">
            or <span className="text-primary font-black underline">browse files</span> from your
            device.
          </p>
        </div>

        <div className="flex flex-wrap items-center justify-center gap-2 pt-2">
          {['PDF Statements', 'CSV Transactions', 'Pay Slip (PNG/JPG)', 'Salary Slip (TXT)'].map(
            (fmt, i) => (
              <Badge
                key={i}
                variant="secondary"
                className="text-[9px] font-bold text-text-muted bg-muted/60 border border-border"
              >
                {fmt}
              </Badge>
            )
          )}
          <Badge
            variant="secondary"
            className="text-[9px] font-bold text-text-muted bg-muted/60 border border-border"
          >
            Max 10 MB
          </Badge>
        </div>

        {uploadError && (
          <div className="flex items-center gap-2 p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-600 text-xs font-bold mt-2 max-w-lg">
            <LucideIcons.AlertCircle className="h-4 w-4 shrink-0" />
            <span>{uploadError}</span>
          </div>
        )}
      </div>

      {/* Documents Table */}
      <div className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-black text-text-primary uppercase tracking-wider">
            Uploaded Documents ({documents.length})
          </h3>
        </div>

        {/* Loading skeleton */}
        {isLoading && (
          <div className="flex flex-col gap-3">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="clay-surface bg-card p-4 rounded-2xl border border-border/40 animate-pulse flex items-center justify-between"
              >
                <div className="flex items-center gap-3 w-1/3">
                  <div className="h-10 w-10 rounded-xl bg-muted" />
                  <div className="flex flex-col gap-1.5 flex-1">
                    <div className="h-3 w-3/4 bg-muted rounded" />
                    <div className="h-2 w-1/2 bg-muted rounded" />
                  </div>
                </div>
                <div className="h-6 w-24 bg-muted rounded-full" />
                <div className="h-8 w-24 bg-muted rounded-xl" />
              </div>
            ))}
          </div>
        )}

        {/* Error state */}
        {isError && !isLoading && (
          <div className="clay-surface bg-card p-8 rounded-3xl border border-rose-500/20 text-center flex flex-col items-center justify-center gap-3">
            <LucideIcons.AlertCircle className="h-8 w-8 text-rose-500" />
            <span className="text-sm font-black text-text-primary">Failed to load documents</span>
            <span className="text-xs font-bold text-text-muted">
              Could not retrieve your documents list.
            </span>
          </div>
        )}

        {/* Empty state */}
        {!isLoading && !isError && documents.length === 0 && (
          <div className="clay-surface bg-card p-12 rounded-3xl border border-white/60 dark:border-white/5 shadow-card text-center flex flex-col items-center justify-center gap-4">
            <div className="h-16 w-16 rounded-3xl bg-muted flex items-center justify-center text-text-muted">
              <LucideIcons.FileQuestion className="h-8 w-8" />
            </div>
            <div className="flex flex-col gap-1 max-w-sm">
              <h4 className="text-sm font-black text-text-primary uppercase tracking-wider">
                No Documents Uploaded
              </h4>
              <p className="text-xs font-bold text-text-muted">
                Upload your bank statements or salary slips above to extract transactions and review
                them.
              </p>
            </div>
          </div>
        )}

        {/* Document rows */}
        {!isLoading && !isError && documents.length > 0 && (
          <div className="flex flex-col gap-3">
            {documents.map((doc) => {
              const DocIcon = getDocTypeIcon(doc.document_type)
              const statusInfo = getStatusBadge(doc.status)
              const isProcessing = processMutation.isPending && processMutation.variables === doc.id

              return (
                <div
                  key={doc.id}
                  className="clay-surface bg-card p-4 rounded-2xl border border-white/60 dark:border-white/5 shadow-card flex flex-col md:flex-row md:items-center justify-between gap-4 hover:border-primary/20 transition-all"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="p-3 rounded-2xl bg-primary/10 text-primary shrink-0">
                      <DocIcon className="h-5 w-5" />
                    </div>
                    <div className="flex flex-col gap-0.5 min-w-0">
                      <span className="text-xs font-black text-text-primary truncate">
                        {doc.original_filename}
                      </span>
                      <div className="flex items-center gap-2 text-[10px] font-bold text-text-muted">
                        <span>{formatDocType(doc.document_type)}</span>
                        <span>•</span>
                        <span>{formatBytes(doc.file_size)}</span>
                        <span>•</span>
                        <span>
                          {new Date(doc.created_at).toLocaleDateString('en-IN', {
                            day: 'numeric',
                            month: 'short',
                            year: 'numeric',
                          })}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center justify-between md:justify-end gap-3 shrink-0 pt-2 md:pt-0 border-t md:border-t-0 border-border/40">
                    <Badge
                      variant="secondary"
                      className={cn(
                        'text-[10px] font-black uppercase tracking-wider py-1 px-3 rounded-xl border',
                        statusInfo.color
                      )}
                    >
                      {statusInfo.label}
                    </Badge>

                    {/* Action buttons */}
                    <div className="flex items-center gap-2">
                      {doc.status === 'UPLOADED' && (
                        <Button
                          variant="primary"
                          size="xs"
                          onClick={() => handleProcess(doc.id)}
                          disabled={isProcessing}
                          iconLeft={
                            isProcessing ? (
                              <LucideIcons.Loader2 className="h-3 w-3 animate-spin" />
                            ) : (
                              <LucideIcons.Play className="h-3 w-3" />
                            )
                          }
                          className="font-black uppercase tracking-wider text-[10px]"
                        >
                          {isProcessing ? 'Processing' : 'Extract'}
                        </Button>
                      )}

                      {(doc.status === 'EXTRACTED' ||
                        doc.status === 'REVIEW_REQUIRED' ||
                        doc.status === 'CONFIRMED') && (
                        <Button
                          variant={doc.status === 'CONFIRMED' ? 'outline' : 'primary'}
                          size="xs"
                          onClick={() => handleOpenReview(doc)}
                          iconLeft={<LucideIcons.Eye className="h-3 w-3" />}
                          className="font-black uppercase tracking-wider text-[10px]"
                        >
                          {doc.status === 'CONFIRMED' ? 'View Results' : 'Review & Import'}
                        </Button>
                      )}

                      {doc.status === 'FAILED' && (
                        <Button
                          variant="secondary"
                          size="xs"
                          onClick={() => handleProcess(doc.id)}
                          disabled={isProcessing}
                          iconLeft={<LucideIcons.RotateCcw className="h-3 w-3" />}
                          className="font-black uppercase tracking-wider text-[10px]"
                        >
                          Retry
                        </Button>
                      )}

                      <button
                        onClick={() => handleDelete(doc.id, doc.original_filename)}
                        disabled={deleteMutation.isPending}
                        className="p-2 rounded-xl hover:bg-rose-500/10 text-text-muted hover:text-rose-600 transition-colors cursor-pointer"
                        title="Delete document"
                      >
                        <LucideIcons.Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* ── Review & Confirmation Modal ────────────────────────────────────── */}
      <Modal isOpen={Boolean(reviewDocId)} onClose={() => setReviewDocId(null)} size="xl">
        <ModalHeader onClose={() => setReviewDocId(null)}>
          <div className="flex items-center gap-2">
            <LucideIcons.FileSearch className="h-5 w-5 text-primary" />
            <h3 className="text-base font-black text-text-primary uppercase tracking-wider">
              Document Extraction Review
            </h3>
          </div>
          <span className="text-[10px] font-bold text-text-muted">
            Inspect extracted metadata and transactions before confirming database import.
          </span>
        </ModalHeader>

        <ModalBody className="max-h-[70vh]">
          {isLoadingExtraction && (
            <div className="py-12 flex flex-col items-center justify-center gap-3 text-center">
              <LucideIcons.Loader2 className="h-8 w-8 animate-spin text-primary" />
              <span className="text-xs font-black text-text-primary uppercase tracking-wider">
                Loading Extraction Candidates...
              </span>
            </div>
          )}

          {confirmationSuccess &&
            (() => {
              const incomeCount = confirmationSuccess.imported_income_count || 0
              const expenseCount = confirmationSuccess.imported_expense_count || 0
              const assetCount = confirmationSuccess.imported_asset_count || 0
              const liabilityCount = confirmationSuccess.imported_liability_count || 0
              const txsCount = confirmationSuccess.imported_transactions_count || 0
              const metadataCount =
                confirmationSuccess.imported_metadata_count ||
                confirmationSuccess.imported_fields_count ||
                0

              const financialRecordsImported =
                incomeCount + expenseCount + assetCount + liabilityCount + txsCount
              const totalItemsImported = financialRecordsImported + metadataCount
              const hasWarnings =
                confirmationSuccess.warnings && confirmationSuccess.warnings.length > 0

              // STATE C: ZERO IMPORT
              if (totalItemsImported === 0) {
                return (
                  <div className="p-6 rounded-2xl bg-blue-500/10 border border-blue-500/20 text-center flex flex-col items-center justify-center gap-3 my-4">
                    <div className="h-12 w-12 rounded-2xl bg-blue-500/20 text-blue-600 flex items-center justify-center">
                      <LucideIcons.Info className="h-6 w-6" />
                    </div>
                    <h4 className="text-sm font-black text-blue-600 uppercase tracking-wider">
                      ⓘ Nothing Was Imported
                    </h4>
                    <p className="text-xs font-bold text-text-primary max-w-md">
                      The document was processed successfully, but no financial records or metadata
                      fields were selected.
                    </p>
                    {hasWarnings && (
                      <div className="text-left w-full mt-2 text-[11px] font-bold text-blue-700 dark:text-blue-300 bg-blue-500/10 p-3 rounded-xl border border-blue-500/20">
                        <span className="font-black uppercase tracking-wider block mb-1">
                          Skipped / Unsupported Fields:
                        </span>
                        <ul className="list-disc pl-4 space-y-0.5">
                          {confirmationSuccess.warnings.map((w, i) => (
                            <li key={i}>{w}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )
              }

              const recordSummary = (
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 w-full my-3">
                  <div className="p-2.5 rounded-xl bg-card border border-border flex flex-col items-center justify-center">
                    <span className="text-[10px] font-black text-text-muted uppercase tracking-wider">
                      Income
                    </span>
                    <span className="text-sm font-black text-emerald-600">{incomeCount}</span>
                  </div>
                  <div className="p-2.5 rounded-xl bg-card border border-border flex flex-col items-center justify-center">
                    <span className="text-[10px] font-black text-text-muted uppercase tracking-wider">
                      Expenses
                    </span>
                    <span className="text-sm font-black text-rose-600">{expenseCount}</span>
                  </div>
                  <div className="p-2.5 rounded-xl bg-card border border-border flex flex-col items-center justify-center">
                    <span className="text-[10px] font-black text-text-muted uppercase tracking-wider">
                      Assets
                    </span>
                    <span className="text-sm font-black text-indigo-600">{assetCount}</span>
                  </div>
                  <div className="p-2.5 rounded-xl bg-card border border-border flex flex-col items-center justify-center">
                    <span className="text-[10px] font-black text-text-muted uppercase tracking-wider">
                      Liabilities
                    </span>
                    <span className="text-sm font-black text-amber-600">{liabilityCount}</span>
                  </div>
                  <div className="p-2.5 rounded-xl bg-card border border-border flex flex-col items-center justify-center">
                    <span className="text-[10px] font-black text-text-muted uppercase tracking-wider">
                      Transactions
                    </span>
                    <span className="text-sm font-black text-primary">{txsCount}</span>
                  </div>
                  <div className="p-2.5 rounded-xl bg-card border border-border flex flex-col items-center justify-center">
                    <span className="text-[10px] font-black text-text-muted uppercase tracking-wider">
                      Metadata
                    </span>
                    <span className="text-sm font-black text-text-primary">{metadataCount}</span>
                  </div>
                </div>
              )

              // STATE B: PARTIAL SUCCESS (IMPORTED WITH WARNINGS)
              if (hasWarnings) {
                return (
                  <div className="p-6 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-center flex flex-col items-center justify-center gap-3 my-4">
                    <div className="h-12 w-12 rounded-2xl bg-amber-500/20 text-amber-600 flex items-center justify-center">
                      <LucideIcons.AlertTriangle className="h-6 w-6" />
                    </div>
                    <h4 className="text-sm font-black text-amber-600 uppercase tracking-wider">
                      ⚠ Import Completed with Warnings
                    </h4>
                    <p className="text-xs font-bold text-text-primary max-w-md">
                      Imported {financialRecordsImported} financial record(s) and {metadataCount}{' '}
                      metadata field(s).
                    </p>
                    {recordSummary}
                    <div className="text-left w-full text-[11px] font-bold text-amber-700 dark:text-amber-300 bg-amber-500/10 p-3 rounded-xl border border-amber-500/20">
                      <span className="font-black uppercase tracking-wider block mb-1">
                        Import Warnings / Information Notes:
                      </span>
                      <ul className="list-disc pl-4 space-y-0.5">
                        {confirmationSuccess.warnings.map((w, i) => (
                          <li key={i}>{w}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                )
              }

              // STATE A: FULL SUCCESS
              return (
                <div className="p-6 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-center flex flex-col items-center justify-center gap-3 my-4">
                  <div className="h-12 w-12 rounded-2xl bg-emerald-500/20 text-emerald-600 flex items-center justify-center">
                    <LucideIcons.CheckCheck className="h-6 w-6" />
                  </div>
                  <h4 className="text-sm font-black text-emerald-600 uppercase tracking-wider">
                    ✓ Import Completed Successfully
                  </h4>
                  <p className="text-xs font-bold text-text-primary max-w-md">
                    Imported {financialRecordsImported} financial record(s) and {metadataCount}{' '}
                    metadata field(s) into your financial records.
                  </p>
                  {recordSummary}
                </div>
              )
            })()}

          {!isLoadingExtraction && extractionData && !confirmationSuccess && (
            <div className="flex flex-col gap-6 text-left">
              {/* Classification Info Header */}
              <div className="clay-surface bg-card p-4 rounded-2xl border border-border flex flex-wrap items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 rounded-xl bg-primary/10 text-primary">
                    <LucideIcons.Tag className="h-4 w-4" />
                  </div>
                  <div className="flex flex-col">
                    <span className="text-[10px] font-black text-text-muted uppercase tracking-wider">
                      Classified Type
                    </span>
                    <span className="text-xs font-black text-text-primary">
                      {formatDocType(extractionData.document_type)}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <div className="p-2.5 rounded-xl bg-emerald-500/10 text-emerald-600">
                    <LucideIcons.ShieldCheck className="h-4 w-4" />
                  </div>
                  <div className="flex flex-col">
                    <span className="text-[10px] font-black text-text-muted uppercase tracking-wider">
                      Confidence
                    </span>
                    <span className="text-xs font-black text-emerald-600">
                      {Math.round(extractionData.classification_confidence * 100)}% High
                    </span>
                  </div>
                </div>

                {(extractionData.period_start || extractionData.period_end) && (
                  <div className="flex items-center gap-3">
                    <div className="p-2.5 rounded-xl bg-indigo-500/10 text-indigo-600">
                      <LucideIcons.Calendar className="h-4 w-4" />
                    </div>
                    <div className="flex flex-col">
                      <span className="text-[10px] font-black text-text-muted uppercase tracking-wider">
                        Statement Period
                      </span>
                      <span className="text-xs font-black text-text-primary">
                        {extractionData.period_start || 'Start'} to{' '}
                        {extractionData.period_end || 'End'}
                      </span>
                    </div>
                  </div>
                )}
              </div>

              {/* Warnings Banner if any */}
              {extractionData.warnings && extractionData.warnings.length > 0 && (
                <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/20 flex flex-col gap-1.5">
                  <div className="flex items-center gap-2 text-amber-600">
                    <LucideIcons.AlertTriangle className="h-4 w-4 shrink-0" />
                    <span className="text-xs font-black uppercase tracking-wider">
                      Validation Warnings Detected
                    </span>
                  </div>
                  <ul className="list-disc pl-5 text-[11px] font-bold text-amber-700 dark:text-amber-400 space-y-0.5">
                    {extractionData.warnings.map((w, idx) => (
                      <li key={idx}>{w}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Income Candidates */}
              {extractionData.income_candidates && extractionData.income_candidates.length > 0 && (
                <div className="flex flex-col gap-3">
                  <span className="text-xs font-black text-emerald-600 uppercase tracking-wider flex items-center gap-2">
                    <LucideIcons.TrendingUp className="h-4 w-4" />
                    Income Candidates ({extractionData.income_candidates.length})
                  </span>
                  <div className="grid grid-cols-1 gap-3">
                    {extractionData.income_candidates.map((inc) => {
                      const isSelected = !deselectedIncomeIds.includes(inc.candidate_id)
                      return (
                        <div
                          key={inc.candidate_id}
                          onClick={() =>
                            setDeselectedIncomeIds((prev) =>
                              prev.includes(inc.candidate_id)
                                ? prev.filter((id) => id !== inc.candidate_id)
                                : [...prev, inc.candidate_id]
                            )
                          }
                          className={cn(
                            'p-3.5 rounded-2xl border transition-all cursor-pointer flex flex-wrap items-center justify-between gap-3',
                            isSelected
                              ? 'bg-emerald-500/10 border-emerald-500/40 shadow-xs'
                              : 'bg-card border-border hover:border-border/80 opacity-60'
                          )}
                        >
                          <div className="flex items-center gap-3">
                            <input
                              type="checkbox"
                              checked={isSelected}
                              onChange={() => {}}
                              className="rounded accent-emerald-600 h-4 w-4 cursor-pointer"
                            />
                            <div className="flex flex-col">
                              <span className="text-xs font-black text-text-primary">
                                {inc.source}
                              </span>
                              <span className="text-[10px] font-bold text-text-muted">
                                Category: {inc.category} • Date: {inc.income_date}
                              </span>
                            </div>
                          </div>
                          <span className="text-sm font-black text-emerald-600">
                            ₹
                            {Number(inc.amount).toLocaleString('en-IN', {
                              minimumFractionDigits: 2,
                            })}
                          </span>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}

              {/* Expense Candidates */}
              {extractionData.expense_candidates &&
                extractionData.expense_candidates.length > 0 && (
                  <div className="flex flex-col gap-3">
                    <span className="text-xs font-black text-rose-600 uppercase tracking-wider flex items-center gap-2">
                      <LucideIcons.CreditCard className="h-4 w-4" />
                      Expense Candidates ({extractionData.expense_candidates.length})
                    </span>
                    <div className="grid grid-cols-1 gap-3">
                      {extractionData.expense_candidates.map((exp) => {
                        const isSelected = !deselectedExpenseIds.includes(exp.candidate_id)
                        return (
                          <div
                            key={exp.candidate_id}
                            onClick={() =>
                              setDeselectedExpenseIds((prev) =>
                                prev.includes(exp.candidate_id)
                                  ? prev.filter((id) => id !== exp.candidate_id)
                                  : [...prev, exp.candidate_id]
                              )
                            }
                            className={cn(
                              'p-3.5 rounded-2xl border transition-all cursor-pointer flex flex-wrap items-center justify-between gap-3',
                              isSelected
                                ? 'bg-rose-500/10 border-rose-500/40 shadow-xs'
                                : 'bg-card border-border hover:border-border/80 opacity-60'
                            )}
                          >
                            <div className="flex items-center gap-3">
                              <input
                                type="checkbox"
                                checked={isSelected}
                                onChange={() => {}}
                                className="rounded accent-rose-600 h-4 w-4 cursor-pointer"
                              />
                              <div className="flex flex-col">
                                <span className="text-xs font-black text-text-primary">
                                  {exp.merchant}
                                </span>
                                <span className="text-[10px] font-bold text-text-muted">
                                  Category: {exp.category} • Date: {exp.expense_date}
                                </span>
                              </div>
                            </div>
                            <span className="text-sm font-black text-rose-600">
                              ₹
                              {Number(exp.amount).toLocaleString('en-IN', {
                                minimumFractionDigits: 2,
                              })}
                            </span>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                )}

              {/* Asset Candidates */}
              {extractionData.asset_candidates && extractionData.asset_candidates.length > 0 && (
                <div className="flex flex-col gap-3">
                  <span className="text-xs font-black text-indigo-600 uppercase tracking-wider flex items-center gap-2">
                    <LucideIcons.Landmark className="h-4 w-4" />
                    Asset Candidates ({extractionData.asset_candidates.length})
                  </span>
                  <div className="grid grid-cols-1 gap-3">
                    {extractionData.asset_candidates.map((ast) => {
                      const isSelected = !deselectedAssetIds.includes(ast.candidate_id)
                      return (
                        <div
                          key={ast.candidate_id}
                          onClick={() =>
                            setDeselectedAssetIds((prev) =>
                              prev.includes(ast.candidate_id)
                                ? prev.filter((id) => id !== ast.candidate_id)
                                : [...prev, ast.candidate_id]
                            )
                          }
                          className={cn(
                            'p-3.5 rounded-2xl border transition-all cursor-pointer flex flex-wrap items-center justify-between gap-3',
                            isSelected
                              ? 'bg-indigo-500/10 border-indigo-500/40 shadow-xs'
                              : 'bg-card border-border hover:border-border/80 opacity-60'
                          )}
                        >
                          <div className="flex items-center gap-3">
                            <input
                              type="checkbox"
                              checked={isSelected}
                              onChange={() => {}}
                              className="rounded accent-indigo-600 h-4 w-4 cursor-pointer"
                            />
                            <div className="flex flex-col">
                              <span className="text-xs font-black text-text-primary">
                                {ast.name}
                              </span>
                              <span className="text-[10px] font-bold text-text-muted">
                                Type: {ast.asset_type}
                              </span>
                            </div>
                          </div>
                          <span className="text-sm font-black text-indigo-600">
                            ₹
                            {Number(ast.value).toLocaleString('en-IN', {
                              minimumFractionDigits: 2,
                            })}
                          </span>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}

              {/* Liability Candidates */}
              {extractionData.liability_candidates &&
                extractionData.liability_candidates.length > 0 && (
                  <div className="flex flex-col gap-3">
                    <span className="text-xs font-black text-amber-600 uppercase tracking-wider flex items-center gap-2">
                      <LucideIcons.AlertCircle className="h-4 w-4" />
                      Liability Candidates ({extractionData.liability_candidates.length})
                    </span>
                    <div className="grid grid-cols-1 gap-3">
                      {extractionData.liability_candidates.map((liab) => {
                        const isSelected = !deselectedLiabilityIds.includes(liab.candidate_id)
                        return (
                          <div
                            key={liab.candidate_id}
                            onClick={() =>
                              setDeselectedLiabilityIds((prev) =>
                                prev.includes(liab.candidate_id)
                                  ? prev.filter((id) => id !== liab.candidate_id)
                                  : [...prev, liab.candidate_id]
                              )
                            }
                            className={cn(
                              'p-3.5 rounded-2xl border transition-all cursor-pointer flex flex-wrap items-center justify-between gap-3',
                              isSelected
                                ? 'bg-amber-500/10 border-amber-500/40 shadow-xs'
                                : 'bg-card border-border hover:border-border/80 opacity-60'
                            )}
                          >
                            <div className="flex items-center gap-3">
                              <input
                                type="checkbox"
                                checked={isSelected}
                                onChange={() => {}}
                                className="rounded accent-amber-600 h-4 w-4 cursor-pointer"
                              />
                              <div className="flex flex-col">
                                <span className="text-xs font-black text-text-primary">
                                  {liab.name}
                                </span>
                                <span className="text-[10px] font-bold text-text-muted">
                                  Type: {liab.liability_type}
                                </span>
                              </div>
                            </div>
                            <span className="text-sm font-black text-amber-600">
                              ₹
                              {Number(liab.amount).toLocaleString('en-IN', {
                                minimumFractionDigits: 2,
                              })}
                            </span>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                )}

              {/* Field Mapping Explanations & Status */}
              {extractionData.field_explanations &&
                extractionData.field_explanations.length > 0 && (
                  <div className="flex flex-col gap-2">
                    <span className="text-xs font-black text-text-primary uppercase tracking-wider">
                      Field Destination Explanations
                    </span>
                    <div className="space-y-1.5 bg-muted/30 p-3 rounded-2xl border border-border">
                      {extractionData.field_explanations.map((exp, idx) => (
                        <div
                          key={idx}
                          className="text-[11px] font-medium text-text-secondary flex flex-wrap items-center justify-between gap-2 border-b border-border/40 pb-1 last:border-b-0 last:pb-0"
                        >
                          <span className="font-bold text-text-primary uppercase tracking-wider">
                            {exp.field_name.replace(/_/g, ' ')}
                          </span>
                          <div className="flex items-center gap-2">
                            <Badge variant="outline" className="text-[9px] font-black">
                              {exp.destination}
                            </Badge>
                            <span className="text-text-muted">{exp.explanation}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

              {/* Extracted Metadata Fields */}
              {extractionData.fields && extractionData.fields.length > 0 && (
                <div className="flex flex-col gap-3">
                  <span className="text-xs font-black text-text-primary uppercase tracking-wider">
                    Extracted Metadata Fields ({extractionData.fields.length})
                  </span>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {extractionData.fields.map((f, idx) => {
                      const isSelected = confirmedFieldNames.includes(f.name)
                      return (
                        <div
                          key={idx}
                          onClick={() => handleToggleField(f.name)}
                          className={cn(
                            'p-3.5 rounded-2xl border transition-all cursor-pointer flex items-center justify-between gap-3',
                            isSelected
                              ? 'bg-primary/5 border-primary/40 shadow-xs'
                              : 'bg-card border-border hover:border-border/80'
                          )}
                        >
                          <div className="flex items-center gap-3">
                            <input
                              type="checkbox"
                              checked={isSelected}
                              onChange={() => handleToggleField(f.name)}
                              className="rounded accent-primary h-4 w-4 cursor-pointer"
                            />
                            <div className="flex flex-col">
                              <span className="text-[10px] font-black text-text-muted uppercase tracking-wider">
                                {f.name.replace(/_/g, ' ')}
                              </span>
                              <span className="text-xs font-black text-text-primary">
                                {typeof f.value === 'number' || typeof f.value === 'string'
                                  ? f.value
                                  : JSON.stringify(f.value)}
                              </span>
                            </div>
                          </div>
                          <Badge
                            variant="secondary"
                            className="text-[9px] font-black bg-emerald-500/10 text-emerald-600 border-emerald-500/20"
                          >
                            {Math.round(f.confidence * 100)}% Conf
                          </Badge>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}

              {/* Extracted Transaction Candidates Table */}
              {extractionData.transactions && extractionData.transactions.length > 0 && (
                <div className="flex flex-col gap-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-black text-text-primary uppercase tracking-wider">
                      Transaction Candidates ({extractionData.transactions.length})
                    </span>
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => handleSelectAllTxs(true)}
                        className="text-[10px] font-black text-primary hover:underline uppercase tracking-wider cursor-pointer"
                      >
                        Select All
                      </button>
                      <span className="text-border">•</span>
                      <button
                        type="button"
                        onClick={() => handleSelectAllTxs(false)}
                        className="text-[10px] font-black text-text-muted hover:underline uppercase tracking-wider cursor-pointer"
                      >
                        Deselect All
                      </button>
                    </div>
                  </div>

                  <div className="border border-border rounded-2xl overflow-hidden shadow-xs">
                    <div className="overflow-x-auto max-h-60 scrollbar-none">
                      <table className="w-full text-left text-xs border-collapse">
                        <thead className="bg-muted/50 border-b border-border text-[10px] font-black text-text-muted uppercase tracking-wider sticky top-0 bg-card">
                          <tr>
                            <th className="p-3 w-10 text-center">
                              <input
                                type="checkbox"
                                checked={
                                  confirmedTxIds.length === extractionData.transactions.length &&
                                  extractionData.transactions.length > 0
                                }
                                onChange={(e) => handleSelectAllTxs(e.target.checked)}
                                className="rounded accent-primary h-3.5 w-3.5 cursor-pointer"
                              />
                            </th>
                            <th className="p-3">Date</th>
                            <th className="p-3">Description</th>
                            <th className="p-3">Type</th>
                            <th className="p-3 text-right">Amount</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-border/60">
                          {extractionData.transactions.map((tx) => {
                            const isSelected = confirmedTxIds.includes(tx.candidate_id)
                            const isIncome = Boolean(tx.credit)
                            const amount = tx.credit || tx.debit || '0'

                            return (
                              <tr
                                key={tx.candidate_id}
                                onClick={() => handleToggleTx(tx.candidate_id)}
                                className={cn(
                                  'cursor-pointer transition-colors hover:bg-muted/30 font-medium',
                                  isSelected && 'bg-primary/5'
                                )}
                              >
                                <td
                                  className="p-3 text-center"
                                  onClick={(e) => e.stopPropagation()}
                                >
                                  <input
                                    type="checkbox"
                                    checked={isSelected}
                                    onChange={() => handleToggleTx(tx.candidate_id)}
                                    className="rounded accent-primary h-3.5 w-3.5 cursor-pointer"
                                  />
                                </td>
                                <td className="p-3 text-[11px] font-bold text-text-muted whitespace-nowrap">
                                  {tx.date}
                                </td>
                                <td className="p-3 text-xs font-bold text-text-primary max-w-xs truncate">
                                  {tx.description}
                                </td>
                                <td className="p-3">
                                  <Badge
                                    variant="secondary"
                                    className={cn(
                                      'text-[9px] font-black uppercase px-2 py-0.5 rounded-lg border',
                                      isIncome
                                        ? 'bg-emerald-500/10 text-emerald-600 border-emerald-500/20'
                                        : 'bg-rose-500/10 text-rose-600 border-rose-500/20'
                                    )}
                                  >
                                    {isIncome ? 'Credit / Income' : 'Debit / Expense'}
                                  </Badge>
                                </td>
                                <td
                                  className={cn(
                                    'p-3 text-right font-black text-xs whitespace-nowrap',
                                    isIncome ? 'text-emerald-600' : 'text-text-primary'
                                  )}
                                >
                                  {isIncome ? '+' : '-'} ₹{Number(amount).toLocaleString('en-IN')}
                                </td>
                              </tr>
                            )
                          })}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}

              {(!extractionData.fields || extractionData.fields.length === 0) &&
                (!extractionData.transactions || extractionData.transactions.length === 0) && (
                  <div className="p-8 rounded-2xl bg-muted/30 text-center flex flex-col items-center justify-center gap-2">
                    <LucideIcons.FileWarning className="h-6 w-6 text-text-muted" />
                    <span className="text-xs font-bold text-text-muted">
                      No structured fields or transaction candidates could be automatically
                      recovered.
                    </span>
                  </div>
                )}
            </div>
          )}
        </ModalBody>

        <ModalFooter>
          {confirmationSuccess ? (
            <Button
              variant="primary"
              size="sm"
              onClick={() => setReviewDocId(null)}
              className="font-black uppercase tracking-wider text-xs"
            >
              Done
            </Button>
          ) : (
            <>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setReviewDocId(null)}
                className="font-black uppercase tracking-wider text-xs"
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={handleConfirmImport}
                disabled={
                  isLoadingExtraction || confirmMutation.isPending || totalSelectedCount === 0
                }
                iconLeft={
                  confirmMutation.isPending ? (
                    <LucideIcons.Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <LucideIcons.Check className="h-4 w-4" />
                  )
                }
                className="font-black uppercase tracking-wider text-xs"
              >
                {confirmMutation.isPending
                  ? 'Importing Records...'
                  : `Confirm & Import (${totalSelectedCount} Selected)`}
              </Button>
            </>
          )}
        </ModalFooter>
      </Modal>
    </motion.div>
  )
}

export default Documents
