import React, { useState, useEffect, useRef } from 'react'
import { ArrowUp, Sparkles, FileCode, Loader2, AlertCircle, RefreshCw, Square } from 'lucide-react'
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
  const [thinkStartTime, setThinkStartTime] = useState<number | null>(null)
  const [thinkDuration, setThinkDuration] = useState(0)
  const [thinkWord, setThinkWord] = useState('Thinking')
  
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    let timer: ReturnType<typeof setInterval>;
    let wordTimer: ReturnType<typeof setInterval>;
    const words = ['Thinking', 'Analyzing', 'Reasoning', 'Reckoning', 'Evaluating'];
    
    if (isLoading && thinkStartTime) {
      timer = setInterval(() => {
        setThinkDuration((Date.now() - thinkStartTime) / 1000)
      }, 100)
      
      let wordIdx = 0;
      wordTimer = setInterval(() => {
        wordIdx = (wordIdx + 1) % words.length;
        setThinkWord(words[wordIdx]);
      }, 2500)
    } else {
      setThinkDuration(0)
      setThinkWord('Thinking')
    }
    
    return () => {
      clearInterval(timer)
      clearInterval(wordTimer)
    }
  }, [isLoading, thinkStartTime])

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

  const abortControllerRef = useRef<AbortController | null>(null)

  const handleStop = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      abortControllerRef.current = null
      setIsLoading(false)
    }
  }

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
    const startTime = Date.now()
    setThinkStartTime(startTime)

    abortControllerRef.current = new AbortController()

    try {
      const response = await sendChatMessage(repoId, msg, undefined, abortControllerRef.current.signal)
      const assistantMsg: ChatMessageType = {
        id: response.id,
        role: 'assistant',
        content: response.message,
        sources: response.sources,
        query_category: response.query_category,
        model_used: response.model_used,
        created_at: new Date().toISOString(),
        thought_time: (Date.now() - startTime) / 1000
      }
      setMessages(prev => [...prev, assistantMsg])
    } catch (err: any) {
      if (err.name === 'CanceledError' || err.message === 'canceled') {
        setMessages(prev => [
          ...prev, 
          {
            id: `aborted-${Date.now()}`,
            role: 'system',
            content: 'You stopped this response',
            sources: null,
            query_category: null,
            model_used: null,
            created_at: new Date().toISOString()
          }
        ])
        return
      }
      const detail = err?.response?.data?.detail || err?.message || 'Failed to get response'
      setError(detail)
    } finally {
      setIsLoading(false)
      setThinkStartTime(null)
      abortControllerRef.current = null
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
            className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-md bg-gray-100 dark:bg-[#18181b]/50 hover:bg-gray-200 dark:hover:bg-[#27272a] border border-gray-200 dark:border-[#27272a]/50 text-xs font-mono text-gray-600 dark:text-[#8b949e] hover:text-gray-900 dark:hover:text-[#c9d1d9] cursor-pointer transition-colors"
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
        <div key={msg.id} className="flex justify-end mb-6 w-full max-w-5xl mx-auto px-4">
          <div className="max-w-[85%] bg-gray-100 dark:bg-[#18181b] text-gray-900 dark:text-[#e6edf3] rounded-3xl px-5 py-3.5 text-[15px] leading-relaxed shadow-sm">
            {msg.content}
          </div>
        </div>
      )
    }
    if (msg.role === 'system') {
      return (
        <div key={msg.id} className="flex items-center justify-center my-6 w-full max-w-5xl mx-auto px-4">
          <div className="h-px bg-gray-200 dark:bg-[#27272a] flex-1"></div>
          <span className="px-4 text-xs font-medium text-gray-500 dark:text-[#8b949e]">{msg.content}</span>
          <div className="h-px bg-gray-200 dark:bg-[#27272a] flex-1"></div>
        </div>
      )
    }
    return (
      <div key={msg.id} className="mb-8 flex gap-4 w-full max-w-5xl mx-auto px-4 group">
        <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-[#0969da] to-[#0550ae] dark:from-[#58a6ff] dark:to-[#318bf8] flex items-center justify-center flex-shrink-0 mt-1 shadow-sm">
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
          
          {msg.thought_time && (
            <div className="flex items-center gap-2 text-gray-500 dark:text-[#8b949e] mb-3 mt-1.5 border border-gray-200 dark:border-[#27272a] rounded-lg px-3 py-1.5 inline-flex bg-gray-50 dark:bg-[#111111]/50 cursor-default hover:bg-gray-100 dark:hover:bg-[#18181b] transition-colors">
              <Sparkles size={14} className="text-gray-400 dark:text-[#6e7681]" />
              <span className="text-[12px] font-medium">Thought for {msg.thought_time.toFixed(1)} seconds</span>
            </div>
          )}

          <div className="text-[15px] leading-relaxed text-gray-800 dark:text-[#c9d1d9] prose prose-slate dark:prose-invert max-w-none prose-p:my-2 prose-pre:bg-gray-50 dark:prose-pre:bg-[#111111] prose-pre:text-gray-800 dark:prose-pre:text-[#c9d1d9] [&_pre_code]:text-gray-800 dark:[&_pre_code]:text-[#c9d1d9] prose-pre:border prose-pre:border-gray-200 dark:prose-pre:border-[#27272a] prose-pre:rounded-xl prose-a:text-[#0969da] dark:prose-a:text-[#58a6ff]">
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
    <div className="flex flex-col h-full bg-white dark:bg-[#000000] overflow-hidden font-sans relative transition-colors duration-150">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto scroll-smooth pt-8 pb-40">
        {showSuggestions && (
          <div className="flex flex-col items-center justify-center h-full text-center px-4 -mt-10">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-[#0969da]/10 to-[#0969da]/20 dark:from-[#58a6ff]/20 dark:to-[#58a6ff]/30 flex items-center justify-center mb-6">
              <Sparkles size={32} className="text-[#0969da] dark:text-[#58a6ff]" />
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
                  className="text-left px-5 py-4 rounded-2xl border border-gray-200 dark:border-[#27272a] bg-gray-50 dark:bg-[#111111]/50 hover:bg-gray-100 dark:hover:bg-[#18181b] hover:border-gray-300 dark:hover:border-[#8b949e] text-[14px] text-gray-700 dark:text-[#c9d1d9] transition-all"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map(renderMessage)}

        {isLoading && (
          <div className="mb-8 flex gap-4 w-full max-w-5xl mx-auto px-4 group">
            <div className="w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 mt-1"></div>
            <div className="flex-1 min-w-0 pt-1">
              <div className="flex items-center gap-2.5 text-[#0969da] dark:text-[#58a6ff]">
                <Sparkles size={16} className="animate-spin" style={{ animationDuration: '3s' }} />
                <span className="text-[15px] font-medium animate-pulse">{thinkWord}</span>
                <span className="text-[14px] font-medium opacity-60 ml-1">{thinkDuration.toFixed(1)}s</span>
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className="mb-8 flex items-start gap-3 w-full max-w-5xl mx-auto px-4">
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
      <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-white via-white dark:from-[#000000] dark:via-[#000000] to-transparent pt-10">
        <div className="max-w-5xl mx-auto relative">
          <div className="flex items-end gap-2 bg-white dark:bg-[#111111] border border-gray-200 dark:border-[#27272a] rounded-3xl p-2 shadow-sm dark:shadow-lg focus-within:border-gray-400 dark:focus-within:border-[#8b949e] focus-within:ring-1 focus-within:ring-gray-400 dark:focus-within:ring-[#8b949e] transition-all">
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
              {isLoading ? (
                <button
                  onClick={handleStop}
                  className="w-9 h-9 rounded-full flex items-center justify-center transition-all bg-[#0969da] hover:bg-[#0550ae] dark:bg-[#58a6ff] dark:hover:bg-[#318bf8] text-white dark:text-[#000000] scale-100"
                  title="Stop generating"
                >
                  <Square size={14} fill="currentColor" />
                </button>
              ) : (
                <button
                  onClick={() => handleSend()}
                  disabled={!input.trim()}
                  className={`w-9 h-9 rounded-full flex items-center justify-center transition-all ${
                    input.trim() 
                      ? 'bg-gray-900 text-white dark:bg-[#e6edf3] dark:text-[#000000] hover:bg-gray-800 dark:hover:bg-white scale-100' 
                      : 'bg-gray-100 text-gray-400 dark:bg-[#18181b] dark:text-[#6e7681] cursor-not-allowed scale-95'
                  }`}
                  title="Send message"
                >
                  <ArrowUp size={18} strokeWidth={2.5} />
                </button>
              )}
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
