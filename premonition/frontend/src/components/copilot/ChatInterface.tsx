import { useRef, useEffect, useState } from 'react'
import { Brain, User, Send, Sparkles } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import type { CopilotCitation } from '@/api/copilotTypes'

// ─── Types ──────────────────────────────────────────────────────────────────

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  citations?: CopilotCitation[]
  timestamp: string
}

interface ChatInterfaceProps {
  messages: ChatMessage[]
  isLoading: boolean
  onSend: (text: string) => void
}

// ─── Suggested Prompts ───────────────────────────────────────────────────────

const SUGGESTED_PROMPTS = [
  'Summarize critical patients',
  'Explain latest alert',
  'What is current ICU occupancy?',
  'Who needs immediate review?',
]

// ─── Subcomponents ───────────────────────────────────────────────────────────

function BotAvatar() {
  return (
    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-indigo-500 to-violet-500 shadow-lg shadow-indigo-500/30">
      <Brain className="h-4 w-4 text-white" />
    </div>
  )
}

function UserAvatar() {
  return (
    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-slate-700 shadow-md">
      <User className="h-4 w-4 text-slate-300" />
    </div>
  )
}

function TypingIndicator() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 8 }}
      className="flex items-start gap-3 px-4"
    >
      <BotAvatar />
      <div className="flex items-center gap-1.5 rounded-2xl border border-slate-700/50 bg-[#0f172a] px-4 py-3">
        {[0, 0.15, 0.3].map((delay, i) => (
          <span
            key={i}
            className="block h-2 w-2 rounded-full bg-indigo-400"
            style={{
              animation: `bounce 1s ease-in-out infinite`,
              animationDelay: `${delay}s`,
            }}
          />
        ))}
      </div>
    </motion.div>
  )
}

function CitationPill({ citation }: { citation: CopilotCitation }) {
  return (
    <span
      title={citation.excerpt}
      className="inline-flex cursor-default items-center rounded-lg border border-indigo-500/30 bg-indigo-500/20 px-2 py-0.5 text-xs text-indigo-300 transition-colors hover:bg-indigo-500/30"
    >
      {citation.title.length > 28 ? citation.title.slice(0, 28) + '…' : citation.title}
    </span>
  )
}

function MessageBubble({ msg }: { msg: ChatMessage }) {
  const isUser = msg.role === 'user'

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, ease: 'easeOut' }}
      className={`flex w-full items-end gap-3 px-4 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}
    >
      {isUser ? <UserAvatar /> : <BotAvatar />}

      <div className={`flex max-w-[72%] flex-col gap-1.5 ${isUser ? 'items-end' : 'items-start'}`}>
        {/* Bubble */}
        <div
          className={`rounded-2xl px-4 py-3 text-sm leading-relaxed ${
            isUser
              ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/20'
              : 'border border-slate-700/50 bg-[#0f172a] text-slate-200'
          }`}
        >
          {msg.content}
        </div>

        {/* Citations */}
        {!isUser && msg.citations && msg.citations.length > 0 && (
          <div className="flex flex-wrap gap-1.5 pt-0.5">
            {msg.citations.map((c) => (
              <CitationPill key={c.source_id} citation={c} />
            ))}
          </div>
        )}

        {/* Timestamp */}
        <span className="px-1 text-[10px] text-slate-500">{msg.timestamp}</span>
      </div>
    </motion.div>
  )
}

function EmptyState({ onPrompt }: { onPrompt: (p: string) => void }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.97 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.4, ease: 'easeOut' }}
      className="flex flex-1 flex-col items-center justify-center gap-6 px-6 py-16"
    >
      {/* Icon */}
      <div className="flex h-20 w-20 items-center justify-center rounded-3xl bg-gradient-to-br from-indigo-500 to-violet-600 shadow-2xl shadow-indigo-500/40">
        <Brain className="h-10 w-10 text-white" />
      </div>

      {/* Title */}
      <div className="text-center">
        <h2 className="bg-gradient-to-r from-indigo-300 via-violet-300 to-purple-300 bg-clip-text text-3xl font-bold tracking-tight text-transparent">
          AI Clinical Copilot
        </h2>
        <p className="mt-2 max-w-xs text-sm text-slate-400">
          Ask anything about your patients, alerts, or ICU status. Answers are grounded in your
          hospital's live data.
        </p>
      </div>

      {/* Suggested prompts grid */}
      <div className="grid w-full max-w-lg grid-cols-2 gap-3">
        {SUGGESTED_PROMPTS.map((prompt) => (
          <button
            key={prompt}
            onClick={() => onPrompt(prompt)}
            className="group flex items-start gap-2 rounded-xl border border-slate-700/60 bg-slate-800/50 px-4 py-3 text-left text-sm text-slate-300 transition-all duration-150 hover:border-indigo-500/50 hover:bg-slate-800 hover:text-white"
          >
            <Sparkles className="mt-0.5 h-3.5 w-3.5 shrink-0 text-indigo-400 group-hover:text-indigo-300" />
            {prompt}
          </button>
        ))}
      </div>
    </motion.div>
  )
}

// ─── Main Component ───────────────────────────────────────────────────────────

export function ChatInterface({ messages, isLoading, onSend }: ChatInterfaceProps) {
  const [input, setInput] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Auto-scroll to bottom on new messages or loading state change
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`
  }, [input])

  const handleSend = () => {
    const trimmed = input.trim()
    if (!trimmed || isLoading) return
    onSend(trimmed)
    setInput('')
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="flex h-full flex-col bg-[#020617]">
      {/* Bounce keyframe injected once */}
      <style>{`
        @keyframes bounce {
          0%, 80%, 100% { transform: translateY(0); }
          40% { transform: translateY(-6px); }
        }
      `}</style>

      {/* Message list */}
      <div className="flex-1 overflow-y-auto scroll-smooth">
        {messages.length === 0 && !isLoading ? (
          <EmptyState onPrompt={(p) => { setInput(p); onSend(p) }} />
        ) : (
          <div className="flex flex-col gap-5 py-6">
            <AnimatePresence initial={false}>
              {messages.map((msg) => (
                <MessageBubble key={msg.id} msg={msg} />
              ))}
              {isLoading && <TypingIndicator key="typing" />}
            </AnimatePresence>
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      {/* Sticky input area */}
      <div className="sticky bottom-0 border-t border-slate-800 bg-[#0a0f1a] px-4 py-4">
        <div className="mx-auto flex max-w-3xl items-end gap-3">
          <div className="relative flex-1">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask the copilot anything…"
              rows={1}
              className="w-full resize-none rounded-2xl border border-slate-700/60 bg-slate-800/70 px-4 py-3 pr-12 text-sm text-slate-100 placeholder-slate-500 outline-none ring-0 transition-all duration-150 focus:border-indigo-500/60 focus:bg-slate-800"
            />
          </div>

          <button
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-indigo-500 text-white shadow-lg shadow-indigo-500/30 transition-all duration-150 hover:bg-indigo-400 disabled:cursor-not-allowed disabled:opacity-40"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>

        <p className="mt-2 text-center text-[10px] text-slate-600">
          AI responses are informational only · Always verify with clinical judgment
        </p>
      </div>
    </div>
  )
}
