import React, { useState, useEffect, useRef } from 'react'
import { Send, MessageSquare, FileCode, Loader2, AlertCircle, RefreshCw } from 'lucide-react'
import { sendChatMessage, getChatHistory } from '../services/api'
import type { ChatMessage as ChatMessageType, SourceReference } from '../types/api'

interface ChatInterfaceProps {
  repoId: string
}

const SUGGESTED_QUESTIONS = [
  'What does this project do?',
  'What are the main components?',
  'How is the code organized?',
  'What frameworks and technologies are used?',
]

const ChatInterface: React.FC<ChatInterfaceProps> = ({ repoId }) => {
  const [messages, setMessages] = useState<ChatMessageType[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isLoadingHistory, setIsLoadingHistory] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Load conversation history
  useEffect(() => {
    const loadHistory = async () => {
      try {
        const history = await getChatHistory(repoId)
        setMessages(history.messages)
      } catch {
        // No history yet — that's fine
      } finally {
        setIsLoadingHistory(false)
      }
    }
    loadHistory()
  }, [repoId])

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async (text?: string) => {
    const msg = text || input.trim()
    if (!msg || isLoading) return

    setInput('')
    setError(null)

    // Add user message immediately
    const userMsg: ChatMessageType = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content: msg,
      sources: null,
      query_category: null,
      model_used: null,
      created_at: new Date().toISOString(),
    }
    setMessages(prev => [...prev, userMsg])
    setIsLoading(true)

    try {
      const response = await sendChatMessage(repoId, msg)
      const assistantMsg: ChatMessageType = {
        id: response.id,
        role: 'assistant',
        content: response.message,
        sources: response.sources,
        query_category: response.query_category,
        model_used: response.model_used,
        created_at: new Date().toISOString(),
      }
      setMessages(prev => [...prev, assistantMsg])
    } catch (err: any) {
      const detail = err?.response?.data?.detail || err?.message || 'Failed to get response'
      setError(detail)
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const getCategoryBadge = (category: string | null) => {
    if (!category) return null
    const colors: Record<string, string> = {
      code: 'bg-blue-900/30 text-blue-400 border-blue-800',
      architecture: 'bg-purple-900/30 text-purple-400 border-purple-800',
      repository: 'bg-green-900/30 text-green-400 border-green-800',
      historical: 'bg-orange-900/30 text-orange-400 border-orange-800',
      general: 'bg-gray-800 text-gray-400 border-gray-700',
    }
    return (
      <span className={`inline-flex px-2 py-0.5 rounded text-xs font-medium border ${colors[category] || colors.general}`}>
        {category}
      </span>
    )
  }

  const renderSources = (sources: SourceReference[] | null) => {
    if (!sources || sources.length === 0) return null
    return (
      <div className="mt-3 flex flex-wrap gap-2">
        <span className="text-xs text-[#8b949e]">Sources:</span>
        {sources.map((src, i) => (
          <span
            key={i}
            className="inline-flex items-center gap-1 px-2 py-1 rounded bg-[#21262d] border border-[#30363d] text-xs font-mono text-[#58a6ff] hover:bg-[#30363d] cursor-default transition-colors"
            title={`${src.file_path} (lines ${src.start_line}-${src.end_line})${src.symbol_name ? ` — ${src.symbol_name}` : ''}`}
          >
            <FileCode size={12} />
            {src.file_path.split('/').pop()}:{src.start_line}-{src.end_line}
          </span>
        ))}
      </div>
    )
  }

  const renderMessage = (msg: ChatMessageType) => {
    if (msg.role === 'user') {
      return (
        <div key={msg.id} className="flex justify-end mb-4">
          <div className="max-w-[80%] bg-[#1f6feb] text-white rounded-lg px-4 py-3 text-sm">
            {msg.content}
          </div>
        </div>
      )
    }
    return (
      <div key={msg.id} className="mb-4">
        <div className="max-w-[90%] bg-[#161b22] border border-[#30363d] rounded-lg px-4 py-3">
          <div className="flex items-center gap-2 mb-2">
            <MessageSquare size={14} className="text-[#58a6ff]" />
            <span className="text-xs font-medium text-[#8b949e]">AskRepo</span>
            {getCategoryBadge(msg.query_category)}
            {msg.model_used && (
              <span className="text-xs text-[#6e7681]">{msg.model_used}</span>
            )}
          </div>
          <div className="text-sm text-[#e6edf3] whitespace-pre-wrap leading-relaxed prose-invert">
            {msg.content}
          </div>
          {renderSources(msg.sources)}
        </div>
      </div>
    )
  }

  if (isLoadingHistory) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="animate-spin text-[#8b949e]" size={24} />
      </div>
    )
  }

  const showSuggestions = messages.length === 0

  return (
    <div className="flex flex-col h-[calc(100vh-260px)] bg-[#0d1117] border border-[#30363d] rounded-lg overflow-hidden">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {showSuggestions && (
          <div className="flex flex-col items-center justify-center h-full text-center px-4">
            <MessageSquare size={48} className="text-[#30363d] mb-4" />
            <h3 className="text-lg font-medium text-[#e6edf3] mb-2">Ask about this codebase</h3>
            <p className="text-sm text-[#8b949e] mb-6 max-w-md">
              Ask any question about the repository's code, architecture, dependencies, or technologies.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-lg">
              {SUGGESTED_QUESTIONS.map((q, i) => (
                <button
                  key={i}
                  onClick={() => handleSend(q)}
                  className="text-left px-4 py-3 rounded-lg border border-[#30363d] bg-[#161b22] hover:bg-[#1c2128] hover:border-[#58a6ff] text-sm text-[#c9d1d9] transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map(renderMessage)}

        {isLoading && (
          <div className="mb-4">
            <div className="max-w-[90%] bg-[#161b22] border border-[#30363d] rounded-lg px-4 py-3">
              <div className="flex items-center gap-2">
                <Loader2 size={14} className="animate-spin text-[#58a6ff]" />
                <span className="text-sm text-[#8b949e]">Analyzing codebase...</span>
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className="mb-4 flex items-start gap-2 p-3 bg-[#3d1014] border border-[#f8514950] rounded-lg">
            <AlertCircle size={16} className="text-[#f85149] mt-0.5 flex-shrink-0" />
            <div className="flex-1">
              <p className="text-sm text-[#f85149]">{error}</p>
              <button
                onClick={() => { setError(null); handleSend(messages[messages.length - 1]?.content) }}
                className="flex items-center gap-1 mt-2 text-xs text-[#58a6ff] hover:underline"
              >
                <RefreshCw size={12} /> Retry
              </button>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-[#30363d] p-4 bg-[#161b22]">
        <div className="flex gap-3">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about this codebase..."
            rows={1}
            className="flex-1 resize-none bg-[#0d1117] border border-[#30363d] rounded-lg px-4 py-2.5 text-sm text-[#e6edf3] placeholder-[#6e7681] focus:border-[#58a6ff] focus:ring-1 focus:ring-[#58a6ff] outline-none"
          />
          <button
            onClick={() => handleSend()}
            disabled={!input.trim() || isLoading}
            className="px-4 py-2.5 bg-[#238636] hover:bg-[#2ea043] disabled:opacity-50 disabled:cursor-not-allowed rounded-lg text-white text-sm font-medium flex items-center gap-2 transition-colors"
          >
            <Send size={16} />
          </button>
        </div>
        <p className="text-xs text-[#6e7681] mt-2">
          Press Enter to send, Shift+Enter for new line
        </p>
      </div>
    </div>
  )
}

export default ChatInterface
