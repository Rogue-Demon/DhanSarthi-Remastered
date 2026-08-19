import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient, ENDPOINTS } from '@/services/api'

export const AI_KEYS = {
  conversations: (params = {}) => ['ai-conversations', params],
  conversation: (id) => ['ai-conversation', id],
}

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

export const useConversationDetail = (conversationId) => {
  return useQuery({
    queryKey: AI_KEYS.conversation(conversationId),
    queryFn: () => apiClient.get(ENDPOINTS.ai.conversations.get(conversationId)),
    enabled: Boolean(conversationId),
    staleTime: 0,
  })
}

export const useCreateConversation = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data = {}) => apiClient.post(ENDPOINTS.ai.conversations.create, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['ai-conversations'] }),
  })
}

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

export const useSendMessage = (conversationId) => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ message }) =>
      apiClient.post(ENDPOINTS.ai.conversations.sendMessage(conversationId), { message }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: AI_KEYS.conversation(conversationId) })
      queryClient.invalidateQueries({ queryKey: ['ai-conversations'] })
    },
  })
}

/**
 * L.9.8 streaming client.
 *
 * Guarantees:
 * - progressive token delivery as soon as SSE chunks arrive
 * - AbortSignal cancellation without persisting partial UI state
 * - complete SSE-frame parsing across arbitrary network chunk boundaries
 * - one terminal callback (complete or error)
 * - 501/unsupported streaming can be handled by the caller's fallback path
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

  let reader = null
  let terminalDelivered = false
  let currentEvent = null
  let buffer = ''

  const deliverError = (error) => {
    if (terminalDelivered) return
    terminalDelivered = true
    onError?.(error)
  }

  const deliverComplete = (payload) => {
    if (terminalDelivered) return
    terminalDelivered = true
    onComplete?.(payload)
  }

  const processFrame = (frame) => {
    const lines = frame.split(/\r?\n/)
    let event = null
    let dataLines = []

    for (const rawLine of lines) {
      const line = rawLine.trimEnd()
      if (line.startsWith('event:')) {
        event = line.slice(6).trim()
      } else if (line.startsWith('data:')) {
        dataLines.push(line.slice(5).trimStart())
      }
    }

    if (!dataLines.length) return
    const dataStr = dataLines.join('\n')
    if (dataStr === '[DONE]') {
      deliverComplete({ status: 'completed' })
      return
    }

    let data
    try {
      data = JSON.parse(dataStr)
    } catch {
      if (event === 'token' || !event) onToken?.(dataStr)
      return
    }

    if (event === 'start') {
      onStart?.(data)
    } else if (event === 'token') {
      onToken?.(data.text ?? '')
    } else if (event === 'metadata') {
      onMetadata?.(data)
    } else if (event === 'complete') {
      deliverComplete(data)
    } else if (event === 'error') {
      const error = new Error(data.message || 'AI streaming failed')
      error.code = data.code
      deliverError(error)
    } else if (!event) {
      if (data.text !== undefined) onToken?.(data.text)
      else if (data.citations || data.quality) onMetadata?.(data)
    }
  }

  try {
    const response = await fetch(url, options)
    if (!response.ok) {
      let errorMsg = `Server error ${response.status}`
      try {
        const errJson = await response.json()
        errorMsg = errJson.detail || errJson.message || errorMsg
      } catch {
        // Ignore non-JSON error bodies.
      }
      const err = new Error(errorMsg)
      err.status = response.status
      throw err
    }

    if (!response.body) {
      const err = new Error('Streaming response body is unavailable')
      err.code = 'STREAM_BODY_UNAVAILABLE'
      throw err
    }

    reader = response.body.getReader()
    const decoder = new TextDecoder()

    while (true) {
      if (signal?.aborted) {
        await reader.cancel()
        const err = new DOMException('The stream was aborted.', 'AbortError')
        throw err
      }

      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const frames = buffer.split(/\r?\n\r?\n/)
      buffer = frames.pop() || ''
      frames.forEach(processFrame)

      if (terminalDelivered) break
    }

    buffer += decoder.decode()
    if (buffer.trim() && !terminalDelivered) processFrame(buffer)

    if (!terminalDelivered) {
      deliverComplete({ status: 'completed' })
    }
  } catch (error) {
    if (error?.name === 'AbortError') {
      // Cancellation is intentionally not reported as a provider failure.
      if (reader) {
        try {
          await reader.cancel()
        } catch {
          /* already closed */
        }
      }
      return
    }

    deliverError(error)
    throw error
  }
}
