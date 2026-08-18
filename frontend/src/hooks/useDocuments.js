import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient, ENDPOINTS } from '@/services/api'

// ---------------------------------------------------------------------------
// Query Keys
// ---------------------------------------------------------------------------
export const DOCUMENT_KEYS = {
  all: ['documents'],
  list: (params = {}) => ['documents', 'list', params],
  detail: (id) => ['documents', 'detail', id],
  extraction: (id) => ['documents', 'extraction', id],
}

// ---------------------------------------------------------------------------
// Queries
// ---------------------------------------------------------------------------

/**
 * Fetch a paginated list of user documents.
 */
export const useDocuments = (params = {}) => {
  const { skip = 0, limit = 50, enabled = true } = params
  return useQuery({
    queryKey: DOCUMENT_KEYS.list({ skip, limit }),
    queryFn: () => {
      const qs = new URLSearchParams()
      qs.set('skip', skip)
      qs.set('limit', limit)
      return apiClient.get(`${ENDPOINTS.documents.list}?${qs.toString()}`)
    },
    enabled,
    staleTime: 30_000,
  })
}

/**
 * Fetch metadata for a single document.
 */
export const useDocument = (documentId) => {
  return useQuery({
    queryKey: DOCUMENT_KEYS.detail(documentId),
    queryFn: () => apiClient.get(ENDPOINTS.documents.get(documentId)),
    enabled: Boolean(documentId),
  })
}

/**
 * Fetch extraction results for a document.
 */
export const useDocumentExtraction = (documentId, options = {}) => {
  return useQuery({
    queryKey: DOCUMENT_KEYS.extraction(documentId),
    queryFn: () => apiClient.get(ENDPOINTS.documents.extraction(documentId)),
    enabled: Boolean(documentId) && (options.enabled ?? true),
    staleTime: 60_000,
  })
}

// ---------------------------------------------------------------------------
// Mutations
// ---------------------------------------------------------------------------

/**
 * Upload a new financial document (PDF, CSV, JPEG, PNG, TXT).
 */
export const useUploadDocument = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (file) => {
      const formData = new FormData()
      formData.append('file', file)
      return apiClient.post(ENDPOINTS.documents.upload, formData)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: DOCUMENT_KEYS.all })
    },
  })
}

/**
 * Trigger processing / extraction pipeline on an uploaded document.
 */
export const useProcessDocument = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (documentId) => apiClient.post(ENDPOINTS.documents.process(documentId)),
    onSuccess: (_, documentId) => {
      queryClient.invalidateQueries({ queryKey: DOCUMENT_KEYS.all })
      queryClient.invalidateQueries({ queryKey: DOCUMENT_KEYS.extraction(documentId) })
    },
  })
}

/**
 * Confirm and import selected fields and transactions into authoritative database.
 * Invalidates financial data queries upon success.
 */
export const useConfirmDocument = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ documentId, data }) =>
      apiClient.post(ENDPOINTS.documents.confirm(documentId), data),
    onSuccess: () => {
      // Invalidate document states
      queryClient.invalidateQueries({ queryKey: DOCUMENT_KEYS.all })
      // Invalidate affected financial queries so dashboard and tables refresh immediately
      queryClient.invalidateQueries({ queryKey: ['income'] })
      queryClient.invalidateQueries({ queryKey: ['expenses'] })
      queryClient.invalidateQueries({ queryKey: ['assets'] })
      queryClient.invalidateQueries({ queryKey: ['liabilities'] })
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      queryClient.invalidateQueries({ queryKey: ['cash-flow'] })
      queryClient.invalidateQueries({ queryKey: ['budget'] })
      queryClient.invalidateQueries({ queryKey: ['financial-summary'] })
      queryClient.invalidateQueries({ queryKey: ['financial-intelligence'] })
    },
  })
}

/**
 * Delete / reject an uploaded document and delete its stored file.
 */
export const useDeleteDocument = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (documentId) => apiClient.delete(ENDPOINTS.documents.delete(documentId)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: DOCUMENT_KEYS.all })
    },
  })
}
