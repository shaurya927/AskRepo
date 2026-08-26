import React, { useState, useEffect, useRef } from 'react'
import { ArrowUp, Sparkles, FileCode, Loader2, AlertCircle, RefreshCw } from 'lucide-react'
import { sendChatMessage, getChatHistory } from '../services/api'
import type { ChatMessage as ChatMessageType, SourceReference } from '../types/api'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

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

  useEffect(() => {
    const loadHistory = async () => {
      try {
        const history = await getChatHistory(repoId)
        setMessages(history.messages)
      } catch {
        // No history yet
      } finally {
        setIsLoadingHistory(false)
      }
    }
    loadHistory()
  }, [repoId])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async (text?: string) => {
    const msg = text || input.trim()
    if (!msg || isLoading) return

    setInput('')
    setError(null)

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
      code: 'text-blue-500 dark:text-blue-400',
      architecture: 'text-purple-500 dark:text-purple-400',
      repository: 'text-green-500 dark:text-green-400',
      historical: 'text-orange-500 dark:text-orange-400',
      general: 'text-gray-500 dark:text-gray-400',
    }
    return (
      <span className={`inline-flex items-center text-[11px] font-medium tracking-wide uppercase ${colors[category] || colors.general}`}>
        {category}
      </span>
    )
  }

  const renderSources = (sources: SourceReference[] | null) => {
    if (!sources || sources.length === 0) return null
    return (
      <div className="mt-4 flex flex-wrap gap-2">
        {sources.map((src, i) => (
          <span
            key={i}
            className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-md bg-gray-100 dark:bg-[#21262d]/50 hover:bg-gray-200 dark:hover:bg-[#30363d] border border-gray-200 dark:border-[#30363d]/50 text-xs font-mono text-gray-600 dark:text-[#8b949e] hover:text-gray-900 dark:hover:text-[#c9d1d9] cursor-pointer transition-colors"
            title={`${src.file_path} (lines ${src.start_line}-${src.end_line})${src.symbol_name ? ` — ${src.symbol_name}` : ''}`}
          >
            <FileCode size={12} className="text-[#0969da] dark:text-[#58a6ff]" />
            {src.file_path.split('/').pop()}:{src.start_line}
          </span>
        ))}
      </div>
    )
  }

  const renderMessage = (msg: ChatMessageType) => {
    if (msg.role === 'user') {
      return (
        <div key={msg.id} className="flex justify-end mb-6 w-full max-w-3xl mx-auto px-4">
          <div className="max-w-[85%] bg-gray-100 dark:bg-[#21262d] text-gray-900 dark:text-[#e6edf3] rounded-3xl px-5 py-3.5 text-[15px] leading-relaxed shadow-sm">
            {msg.content}
          </div>
        </div>
      )
    }
    return (
      <div key={msg.id} className="mb-8 flex gap-4 w-full max-w-3xl mx-auto px-4 group">
        <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-[#ca9dfc] to-[#9254de] flex items-center justify-center flex-shrink-0 mt-1 shadow-sm">
          <Sparkles size={16} className="text-white fill-white" />
        </div>
        
        <div className="flex-1 min-w-0 pt-0.5">
          <div className="flex items-center gap-3 mb-1">
            <span className="font-semibold text-gray-900 dark:text-[#e6edf3] text-sm">AskRepo</span>
            {getCategoryBadge(msg.query_category)}
            {msg.model_used && (
              <span className="text-[11px] text-gray-400 dark:text-[#6e7681] opacity-0 group-hover:opacity-100 transition-opacity">{msg.model_used}</span>
            )}
          </div>
          <div className="text-[15px] leading-relaxed text-gray-800 dark:text-[#c9d1d9] prose prose-slate dark:prose-invert max-w-none prose-p:my-2 prose-pre:bg-gray-50 dark:prose-pre:bg-[#161b22] prose-pre:text-gray-800 dark:prose-pre:text-[#c9d1d9] [&_pre_code]:text-gray-800 dark:[&_pre_code]:text-[#c9d1d9] prose-pre:border prose-pre:border-gray-200 dark:prose-pre:border-[#30363d] prose-pre:rounded-xl prose-a:text-[#0969da] dark:prose-a:text-[#58a6ff]">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {msg.content}
            </ReactMarkdown>
          </div>
          {renderSources(msg.sources)}
        </div>
      </div>
    )
  }

  if (isLoadingHistory) {
    return (
      <div className="flex items-center justify-center h-full min-h-[400px]">
        <Loader2 className="animate-spin text-gray-400 dark:text-[#8b949e]" size={24} />
      </div>
    )
  }

  const showSuggestions = messages.length === 0

  return (
    <div className="flex flex-col h-full bg-white dark:bg-[#0d1117] overflow-hidden font-sans relative transition-colors duration-150">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto scroll-smooth pt-8 pb-40">
        {showSuggestions && (
          <div className="flex flex-col items-center justify-center h-full text-center px-4 -mt-10">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-[#ca9dfc]/10 to-[#9254de]/10 dark:from-[#ca9dfc]/20 dark:to-[#9254de]/20 flex items-center justify-center mb-6">
              <Sparkles size={32} className="text-[#9254de] dark:text-[#ca9dfc]" />
            </div>
            <h3 className="text-2xl font-medium text-gray-900 dark:text-[#e6edf3] mb-3">How can I help you?</h3>
            <p className="text-base text-gray-500 dark:text-[#8b949e] mb-10 max-w-md">
              Ask anything about this repository's codebase, architecture, or history.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-2xl mx-auto">
              {SUGGESTED_QUESTIONS.map((q, i) => (
                <button
                  key={i}
                  onClick={() => handleSend(q)}
                  className="text-left px-5 py-4 rounded-2xl border border-gray-200 dark:border-[#30363d] bg-gray-50 dark:bg-[#161b22]/50 hover:bg-gray-100 dark:hover:bg-[#21262d] hover:border-gray-300 dark:hover:border-[#8b949e] text-[14px] text-gray-700 dark:text-[#c9d1d9] transition-all"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map(renderMessage)}

        {isLoading && (
          <div className="mb-8 flex gap-4 w-full max-w-3xl mx-auto px-4">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-[#ca9dfc]/50 to-[#9254de]/50 flex items-center justify-center flex-shrink-0 mt-1">
              <Sparkles size={16} className="text-white/70" />
            </div>
            <div className="flex-1 min-w-0 pt-2">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-[#ca9dfc] animate-pulse"></div>
                <div className="w-2 h-2 rounded-full bg-[#ca9dfc] animate-pulse delay-75"></div>
                <div className="w-2 h-2 rounded-full bg-[#ca9dfc] animate-pulse delay-150"></div>
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className="mb-8 flex items-start gap-3 w-full max-w-3xl mx-auto px-4">
            <div className="w-8 h-8 rounded-xl bg-red-50 dark:bg-[#f85149]/20 flex items-center justify-center flex-shrink-0 mt-1">
              <AlertCircle size={16} className="text-red-500 dark:text-[#f85149]" />
            </div>
            <div className="flex-1 pt-1.5">
              <p className="text-sm text-red-600 dark:text-[#f85149]">{error}</p>
              <button
                onClick={() => { setError(null); handleSend(messages[messages.length - 1]?.content) }}
                className="flex items-center gap-1.5 mt-2 text-xs font-medium text-[#0969da] dark:text-[#58a6ff] hover:underline transition-colors"
              >
                <RefreshCw size={12} /> Try again
              </button>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area (Absolute positioned at bottom) */}
      <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-white via-white dark:from-[#0d1117] dark:via-[#0d1117] to-transparent pt-10">
        <div className="max-w-3xl mx-auto relative">
          <div className="flex items-end gap-2 bg-white dark:bg-[#161b22] border border-gray-200 dark:border-[#30363d] rounded-3xl p-2 shadow-sm dark:shadow-lg focus-within:border-gray-400 dark:focus-within:border-[#8b949e] focus-within:ring-1 focus-within:ring-gray-400 dark:focus-within:ring-[#8b949e] transition-all">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => {
                setInput(e.target.value)
                e.target.style.height = 'auto'
                e.target.style.height = `${Math.min(e.target.scrollHeight, 200)}px`
              }}
              onKeyDown={handleKeyDown}
              placeholder="Ask AskRepo..."
              rows={1}
              className="flex-1 max-h-[200px] resize-none bg-transparent border-none px-4 py-3 text-[15px] text-gray-900 dark:text-[#e6edf3] placeholder-gray-400 dark:placeholder-[#8b949e] focus:outline-none focus:ring-0 leading-relaxed"
              style={{ minHeight: '48px' }}
            />
            <div className="pb-1.5 pr-1.5 flex-shrink-0">
              <button
                onClick={() => handleSend()}
                disabled={!input.trim() || isLoading}
                className={`w-9 h-9 rounded-full flex items-center justify-center transition-all ${
                  input.trim() && !isLoading 
                    ? 'bg-gray-900 text-white dark:bg-[#e6edf3] dark:text-[#0d1117] hover:bg-gray-800 dark:hover:bg-white scale-100' 
                    : 'bg-gray-100 text-gray-400 dark:bg-[#21262d] dark:text-[#6e7681] cursor-not-allowed scale-95'
                }`}
              >
                <ArrowUp size={18} strokeWidth={2.5} />
              </button>
            </div>
          </div>
          <div className="text-center mt-2 mb-1">
            <p className="text-[11px] text-gray-500 dark:text-[#6e7681]">
              AI can make mistakes. Please verify important information.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ChatInterface
