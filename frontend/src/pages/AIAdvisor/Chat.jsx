import React from 'react'
import { useParams } from 'react-router-dom'
import ChatWorkspace from './ChatWorkspace'

/**
 * Chat route page — reads the optional :conversationId param from the URL
 * and passes it down to ChatWorkspace so it can load existing conversation history.
 *
 * Route: /ai-advisor/chat                    → new / welcome screen
 * Route: /ai-advisor/chat/:conversationId    → existing conversation loaded
 */
export function Chat() {
  const { conversationId } = useParams()
  return <ChatWorkspace conversationId={conversationId ? Number(conversationId) : null} />
}

export default Chat
