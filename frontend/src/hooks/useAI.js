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

/**
 * Stream a chat message via SSE endpoint with callbacks for real-time progressive rendering.
 *
 * @param {Object} params
 * @param {string|number} params.conversationId
 * @param {string} params.message
 * @param {Function} [params.onStart] - Callback when stream starts
 * @param {Function} [params.onToken] - Callback for each text token chunk
 * @param {Function} [params.onMetadata] - Callback with citations, latency, quality
 * @param {Function} [params.onComplete] - Callback when message generation completes
 * @param {Function} [params.onError] - Callback on error
 * @param {AbortSignal} [params.signal] - AbortSignal for user cancellation
 */
export const streamChatMessage = async ({
  conversationId,
  message,
  onStart,
  onToken,
  onMetadata,
  onComplete,
  onError,
  signal,
}) => {
  const { envConfig } = await import('@/config')
  const { requestInterceptor } = await import('@/services/api/interceptors')
  const url = `${envConfig.apiBaseUrl}${ENDPOINTS.ai.conversations.stream(conversationId)}`
  const options = requestInterceptor({
    method: 'POST',
    body: JSON.stringify({ message }),
    signal,
  })

  try {
    const response = await fetch(url, options)
    if (!response.ok) {
      let errorMsg = `Server error ${response.status}`
      try {
        const errJson = await response.json()
        errorMsg = errJson.detail || errJson.message || errorMsg
      } catch {
        // Response is not JSON
      }
      const err = new Error(errorMsg)
      err.status = response.status
      throw err
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      let currentEvent = null
      for (const line of lines) {
        const trimmed = line.trim()
        if (!trimmed) {
          currentEvent = null
          continue
        }
        if (trimmed.startsWith('event:')) {
          currentEvent = trimmed.slice(6).trim()
        } else if (trimmed.startsWith('data:')) {
          const dataStr = trimmed.slice(5).trim()
          if (dataStr === '[DONE]') {
            continue
          }
          try {
            const data = JSON.parse(dataStr)
            if (currentEvent === 'start') {
              onStart?.(data)
            } else if (currentEvent === 'token') {
              onToken?.(data.text ?? '')
            } else if (currentEvent === 'metadata') {
              onMetadata?.(data)
            } else if (currentEvent === 'complete') {
              onComplete?.(data)
            } else if (currentEvent === 'error') {
              onError?.(new Error(data.message || 'Stream error'))
            } else if (!currentEvent) {
              if (data.text !== undefined) {
                onToken?.(data.text)
              } else if (data.citations || data.quality) {
                onMetadata?.(data)
              }
            }
          } catch {
            // Raw text chunk fallback
            if (currentEvent === 'token' || !currentEvent) {
              onToken?.(dataStr)
            }
          }
        }
      }
    }
  } catch (error) {
    if (error.name === 'AbortError') {
      console.log('Chat stream cancelled by user.')
      return
    }
    onError?.(error)
    throw error
  }
}
