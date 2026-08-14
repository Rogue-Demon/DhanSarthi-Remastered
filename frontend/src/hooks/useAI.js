import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient, ENDPOINTS } from '@/services/api'

// ---------------------------------------------------------------------------
// Query Keys
// ---------------------------------------------------------------------------
export const AI_KEYS = {
  conversations: (params = {}) => ['ai-conversations', params],
  conversation: (id) => ['ai-conversation', id],
}

// ---------------------------------------------------------------------------
// Queries
// ---------------------------------------------------------------------------

/**
 * Fetch the paginated list of the current user's AI conversations.
 */
export const useConversationList = (params = {}) => {
  const { skip = 0, limit = 50, enabled = true } = params
  return useQuery({
    queryKey: AI_KEYS.conversations({ skip, limit }),
    queryFn: () => {
      const qs = new URLSearchParams()
      qs.set('skip', skip)
      qs.set('limit', limit)
      return apiClient.get(`${ENDPOINTS.ai.conversations.list}?${qs.toString()}`)
    },
    enabled,
    staleTime: 30_000,
  })
}

/**
 * Fetch a single conversation with its full message history.
 */
export const useConversationDetail = (conversationId) => {
  return useQuery({
    queryKey: AI_KEYS.conversation(conversationId),
    queryFn: () => apiClient.get(ENDPOINTS.ai.conversations.get(conversationId)),
    enabled: Boolean(conversationId),
    staleTime: 0, // always fresh — messages change frequently
  })
}

// ---------------------------------------------------------------------------
// Mutations
// ---------------------------------------------------------------------------

/**
 * Create a new conversation thread.
 * Invalidates the conversation list on success.
 */
export const useCreateConversation = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data = {}) => apiClient.post(ENDPOINTS.ai.conversations.create, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ai-conversations'] })
    },
  })
}

/**
 * Soft-delete a conversation.
 * Invalidates the conversation list and the specific conversation cache.
 */
export const useDeleteConversation = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (conversationId) =>
      apiClient.delete(ENDPOINTS.ai.conversations.delete(conversationId)),
    onSuccess: (_data, conversationId) => {
      queryClient.invalidateQueries({ queryKey: ['ai-conversations'] })
      queryClient.removeQueries({ queryKey: AI_KEYS.conversation(conversationId) })
    },
  })
}

/**
 * Send a message in a conversation and receive the AI advisor response.
 * Invalidates the conversation detail cache on success.
 */
export const useSendMessage = (conversationId) => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ message }) =>
      apiClient.post(ENDPOINTS.ai.conversations.sendMessage(conversationId), { message }),
    onSuccess: () => {
      // Refresh the detail view so the new messages appear
      queryClient.invalidateQueries({ queryKey: AI_KEYS.conversation(conversationId) })
      // Also bump the list (updated_at, message_count changes)
      queryClient.invalidateQueries({ queryKey: ['ai-conversations'] })
    },
  })
}
