import { useState, useRef, useCallback } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { Bot, Plus, MessageSquare, Sparkles, Mic, MicOff, Download } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChatInterface } from '@/components/copilot/ChatInterface'
import { copilotApi } from '@/api/copilotEndpoints'
import type { ChatMessage } from '@/components/copilot/ChatInterface'
import { exportHandoverPDF } from '@/utils/pdfExport'

// ─── Voice Copilot Hook ────────────────────────────────────────────────────────
function useVoiceCopilot(onTranscript: (text: string) => void) {
  const [isListening, setIsListening] = useState(false)
  const [interim, setInterim] = useState('')
  const recognitionRef = useRef<any>(null)

  const startListening = useCallback(() => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
    if (!SpeechRecognition) {
      alert('Speech recognition is not supported in this browser. Please use Chrome or Edge.')
      return
    }
    const recognition = new SpeechRecognition()
    recognition.continuous = false
    recognition.interimResults = true
    recognition.lang = 'en-US'

    recognition.onresult = (event: any) => {
      const transcript = Array.from(event.results)
        .map((r: any) => r[0].transcript)
        .join('')
      setInterim(transcript)
      if (event.results[event.results.length - 1].isFinal) {
        setInterim('')
        setIsListening(false)
        if (transcript.trim()) onTranscript(transcript.trim())
      }
    }
    recognition.onerror = () => { setIsListening(false); setInterim('') }
    recognition.onend = () => { setIsListening(false); setInterim('') }

    recognitionRef.current = recognition
    recognition.start()
    setIsListening(true)
  }, [onTranscript])

  const stopListening = useCallback(() => {
    recognitionRef.current?.stop()
    setIsListening(false)
    setInterim('')
  }, [])

  return { isListening, interim, startListening, stopListening }
}

// ─── Patient Context Panel ─────────────────────────────────────────────────────
const SUGGESTED_PATIENT_IDS = [
  'PT-00142', 'PT-00089', 'PT-00211', 'PT-00334', 'PT-00076', 'PT-00199',
]

function PatientContextPanel({ onPatientSelect }: { onPatientSelect: (id: string) => void }) {
  return (
    <div className="flex h-full flex-col border-l border-slate-800 bg-[#020617] p-4">
      <div className="mb-4 flex items-center gap-2">
        <Sparkles className="h-4 w-4 text-indigo-400" />
        <span className="text-sm font-semibold text-slate-200">Patient Context</span>
      </div>
      <p className="mb-4 text-xs leading-relaxed text-slate-500">
        Select a patient to focus the Copilot on their specific clinical data.
      </p>
      <div className="flex flex-col gap-2">
        {SUGGESTED_PATIENT_IDS.map((pid) => (
          <button
            key={pid}
            onClick={() => onPatientSelect(pid)}
            className="group flex items-center justify-between rounded-xl border border-slate-700/50 bg-slate-800/40 px-3 py-2.5 text-left transition-all duration-150 hover:border-indigo-500/40 hover:bg-slate-800"
          >
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-amber-400" />
              <span className="text-sm font-medium text-slate-300 group-hover:text-white">{pid}</span>
            </div>
            <Bot className="h-3.5 w-3.5 text-slate-600 group-hover:text-indigo-400" />
          </button>
        ))}
      </div>
      <div className="mt-auto pt-6">
        <div className="flex items-center gap-2 rounded-xl border border-emerald-500/20 bg-emerald-500/10 px-3 py-2">
          <div className="h-2 w-2 animate-pulse rounded-full bg-emerald-400" />
          <span className="text-xs font-medium text-emerald-400">Groq AI Ready</span>
        </div>
        <p className="mt-2 text-center text-[10px] text-slate-600">
          Powered by Groq AI · Zero data leaves your hospital
        </p>
      </div>
    </div>
  )
}

// ─── Left Sidebar ──────────────────────────────────────────────────────────────
interface SidebarConversation {
  id: string
  firstMessage: string
  time: string
  messageCount: number
}

function LeftSidebar({
  conversations, activeId, onSelect, onNew,
}: {
  conversations: SidebarConversation[]
  activeId?: string
  onSelect: (id: string) => void
  onNew: () => void
}) {
  return (
    <div className="flex h-full w-64 shrink-0 flex-col border-r border-slate-800 bg-[#020617]">
      <div className="flex items-center gap-2.5 border-b border-slate-800 px-4 py-4">
        <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600">
          <Bot className="h-4 w-4 text-white" />
        </div>
        <span className="text-sm font-bold tracking-wide text-slate-100">Copilot</span>
      </div>
      <div className="p-3">
        <button
          onClick={onNew}
          className="flex w-full items-center justify-center gap-2 rounded-xl border border-indigo-500/30 bg-indigo-500/10 py-2.5 text-sm font-medium text-indigo-300 transition-all duration-150 hover:border-indigo-400/50 hover:bg-indigo-500/20 hover:text-indigo-200"
        >
          <Plus className="h-4 w-4" />
          New Chat
        </button>
      </div>
      <div className="flex-1 overflow-y-auto px-2 pb-4">
        {conversations.length === 0 ? (
          <p className="px-3 py-4 text-center text-xs text-slate-500">No conversations yet</p>
        ) : (
          <div className="space-y-1">
            {conversations.map((conv) => (
              <button
                key={conv.id}
                onClick={() => onSelect(conv.id)}
                className={`flex w-full items-start gap-2.5 rounded-xl px-3 py-2.5 text-left transition-all duration-150 ${
                  activeId === conv.id
                    ? 'bg-indigo-500/15 text-indigo-300'
                    : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
                }`}
              >
                <MessageSquare className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                <div className="min-w-0">
                  <p className="truncate text-xs font-medium leading-snug">
                    {conv.firstMessage.slice(0, 30)}{conv.firstMessage.length > 30 ? '…' : ''}
                  </p>
                  <p className="mt-0.5 text-[10px] text-slate-600">{conv.time}</p>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

// ─── Hero Header ───────────────────────────────────────────────────────────────
function HeroHeader() {
  return (
    <motion.div
      initial={{ opacity: 0, y: -16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -16 }}
      transition={{ duration: 0.35, ease: 'easeOut' }}
      className="flex flex-col items-center gap-3 border-b border-slate-800 bg-[#020617] px-6 py-5"
    >
      <h1 className="bg-gradient-to-r from-indigo-300 via-violet-300 to-purple-300 bg-clip-text text-2xl font-bold tracking-tight text-transparent">
        AI Clinical Copilot
      </h1>
      <p className="text-center text-xs text-slate-500">
        Powered by Groq AI · HIPAA-safe · Zero data leaves your hospital
      </p>
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-1.5 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1">
          <div className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-400" />
          <span className="text-[11px] font-semibold tracking-wide text-emerald-400">Groq AI Ready</span>
        </div>
        <div className="flex items-center gap-1.5 rounded-full border border-indigo-500/30 bg-indigo-500/10 px-3 py-1">
          <Mic className="h-3 w-3 text-indigo-400" />
          <span className="text-[11px] font-semibold tracking-wide text-indigo-400">Voice Enabled</span>
        </div>
      </div>
      <div className="mt-1 grid grid-cols-3 gap-3 text-center text-[10px] text-slate-500 w-full max-w-sm">
        <div className="rounded-lg bg-slate-800/50 p-2">
          <p className="text-slate-300 font-semibold">Patient Summary</p>
          <p>Ask for any patient</p>
        </div>
        <div className="rounded-lg bg-slate-800/50 p-2">
          <p className="text-slate-300 font-semibold">Shift Handover</p>
          <p>Generate handover report</p>
        </div>
        <div className="rounded-lg bg-slate-800/50 p-2">
          <p className="text-slate-300 font-semibold">Explain Risk</p>
          <p>Interpret AI predictions</p>
        </div>
      </div>
    </motion.div>
  )
}

// ─── Voice Button ──────────────────────────────────────────────────────────────
function VoiceButton({ onTranscript }: { onTranscript: (t: string) => void }) {
  const { isListening, interim, startListening, stopListening } = useVoiceCopilot(onTranscript)

  return (
    <div className="flex flex-col items-end gap-1">
      {interim && (
        <div className="max-w-xs rounded-lg bg-indigo-500/10 border border-indigo-500/20 px-3 py-1.5">
          <p className="text-xs text-indigo-300 italic">"{interim}"</p>
        </div>
      )}
      <button
        id="voice-copilot-btn"
        onClick={isListening ? stopListening : startListening}
        title={isListening ? 'Stop listening' : 'Start voice input'}
        className={`flex h-10 w-10 items-center justify-center rounded-full border transition-all duration-200 ${
          isListening
            ? 'border-red-500 bg-red-500/20 text-red-400 shadow-[0_0_12px_rgba(239,68,68,0.4)] animate-pulse'
            : 'border-slate-700 bg-slate-800 text-slate-400 hover:border-indigo-500/50 hover:text-indigo-400'
        }`}
      >
        {isListening ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
      </button>
    </div>
  )
}

// ─── PDF Export Button ─────────────────────────────────────────────────────────
function PDFExportButton({ messages }: { messages: ChatMessage[] }) {
  const lastAssistantMsg = [...messages].reverse().find(m => m.role === 'assistant')
  if (!lastAssistantMsg) return null

  const handleExport = () => {
    exportHandoverPDF(lastAssistantMsg.content)
  }

  return (
    <button
      id="pdf-export-btn"
      onClick={handleExport}
      title="Export last response as PDF"
      className="flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-800 px-3 py-1.5 text-xs font-medium text-slate-400 hover:border-indigo-500/50 hover:text-indigo-400 transition-all duration-150"
    >
      <Download className="h-3.5 w-3.5" />
      Export PDF
    </button>
  )
}

// ─── Helpers ───────────────────────────────────────────────────────────────────
function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`
}

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

// ─── Page ──────────────────────────────────────────────────────────────────────
export function CopilotPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [activeConversationId, setActiveConversationId] = useState<string | undefined>()
  const [sidebarConversations, setSidebarConversations] = useState<SidebarConversation[]>([])

  const { data: apiConversations = [] } = useQuery({
    queryKey: ['copilot-conversations'],
    queryFn: copilotApi.conversations,
    refetchInterval: 30_000,
  })

  const mergedConversations: SidebarConversation[] = [
    ...sidebarConversations,
    ...apiConversations
      .filter((c) => !sidebarConversations.find((s) => s.id === c.id))
      .map((c) => ({
        id: c.id,
        firstMessage: c.title,
        time: formatTime(c.updated_at),
        messageCount: c.message_count,
      })),
  ]

  const chatMutation = useMutation({
    mutationFn: copilotApi.chat,
    onSuccess: (data) => {
      const assistantMsg: ChatMessage = {
        id: generateId(),
        role: 'assistant',
        content: data.message,
        citations: data.citations,
        timestamp: new Date().toLocaleTimeString(),
      }
      setMessages((prev) => [...prev, assistantMsg])
      if (!activeConversationId && data.conversation_id) {
        setActiveConversationId(data.conversation_id)
      }
    },
  })

  const handleSend = useCallback((text: string) => {
    const userMsg: ChatMessage = {
      id: generateId(),
      role: 'user',
      content: text,
      timestamp: new Date().toLocaleTimeString(),
    }
    setMessages((prev) => {
      if (prev.length === 0) {
        setSidebarConversations((prevConvs) => [
          {
            id: activeConversationId ?? generateId(),
            firstMessage: text,
            time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            messageCount: 1,
          },
          ...prevConvs,
        ])
      }
      return [...prev, userMsg]
    })
    chatMutation.mutate({ message: text, conversation_id: activeConversationId })
  }, [activeConversationId, chatMutation])

  const handleNewChat = () => {
    setMessages([])
    setActiveConversationId(undefined)
  }

  const handlePatientSelect = (patientId: string) => {
    handleSend(`Give me a comprehensive clinical summary, risk assessment, and recommended actions for patient ${patientId}.`)
  }

  const handleConversationSelect = async (id: string) => {
    setActiveConversationId(id)
    try {
      const detail = await copilotApi.conversation(id)
      const restored: ChatMessage[] = detail.messages.map((m, i) => ({
        id: `${id}-${i}`,
        role: m.role as 'user' | 'assistant',
        content: m.content,
        timestamp: formatTime(detail.updated_at),
      }))
      setMessages(restored)
    } catch {
      setMessages([])
    }
  }

  const hasMessages = messages.length > 0

  return (
    <div className="flex h-screen overflow-hidden bg-[#020617]">
      {/* Left Sidebar */}
      <LeftSidebar
        conversations={mergedConversations}
        activeId={activeConversationId}
        onSelect={handleConversationSelect}
        onNew={handleNewChat}
      />

      {/* Main Area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Hero header when no messages */}
        <AnimatePresence>
          {!hasMessages && <HeroHeader key="hero" />}
        </AnimatePresence>

        {/* PDF Export + Voice row when there are messages */}
        {hasMessages && (
          <div className="flex items-center justify-end gap-2 border-b border-slate-800 bg-[#020617] px-4 py-2">
            <PDFExportButton messages={messages} />
            <VoiceButton onTranscript={handleSend} />
          </div>
        )}

        {/* Chat fills remaining height */}
        <div className="flex-1 overflow-hidden">
          <ChatInterface
            messages={messages}
            isLoading={chatMutation.isPending}
            onSend={handleSend}
          />
        </div>
      </div>

      {/* Right Sidebar — Voice + Patient Panel */}
      <div className="hidden w-72 shrink-0 flex-col xl:flex">
        {/* Voice Copilot Block */}
        <div className="border-b border-slate-800 bg-[#020617] p-4">
          <div className="flex items-center gap-2 mb-2">
            <Mic className="h-4 w-4 text-indigo-400" />
            <span className="text-sm font-semibold text-slate-200">Voice Copilot</span>
          </div>
          <p className="text-xs text-slate-500 mb-3">Say commands like:<br />"Summarize patient PT-00142"<br />"Explain sepsis risk factors"<br />"Generate shift handover"</p>
          <div className="flex justify-center">
            <VoiceButton onTranscript={handleSend} />
          </div>
        </div>
        {/* Patient Context Panel */}
        <div className="flex-1 overflow-auto">
          <PatientContextPanel onPatientSelect={handlePatientSelect} />
        </div>
      </div>
    </div>
  )
}
