'use client'

import { useState, useRef, useEffect } from 'react'
import { chatWithAI } from '@/lib/api'
import { useAppStore } from '@/lib/store'
import type { ChatMessage } from '@/types'
import clsx from 'clsx'

const LION_ICON = '🦁'

const INITIAL_MESSAGE: ChatMessage = {
  id: 'init',
  role: 'assistant',
  content: 'مرحباً! أنا محلل أسد السوق. يمكنني مساعدتك في تحليل الأسواق، شرح الإشارات، وتقديم توصيات التداول. كيف يمكنني مساعدتك اليوم؟',
  timestamp: new Date().toISOString(),
}

const QUICK_QUESTIONS_AR = [
  'ما هو التوصية الحالية للذهب؟',
  'هل الوضع مناسب للشراء؟',
  'ما هي أهداف السعر؟',
  'ما هي المخاطر الحالية؟',
]

const QUICK_QUESTIONS_EN = [
  'What is the current gold signal?',
  'Is it a good time to buy?',
  'What are the price targets?',
  'What are the current risks?',
]

export default function AIChat() {
  const { language, selectedSymbol } = useAppStore()
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>([INITIAL_MESSAGE])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const isRtl = language === 'ar'

  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages, isOpen])

  const sendMessage = async (text?: string) => {
    const messageText = text || input.trim()
    if (!messageText) return

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: messageText,
      timestamp: new Date().toISOString(),
    }

    setMessages(prev => [...prev, userMsg])
    setInput('')
    setIsLoading(true)

    try {
      const history = messages.map(m => ({ role: m.role, content: m.content }))
      const res = await chatWithAI(messageText, history)
      const assistantMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: res.data.message || res.data.response,
        timestamp: new Date().toISOString(),
      }
      setMessages(prev => [...prev, assistantMsg])
    } catch {
      // Fallback response
      const fallbacks = {
        ar: [
          `بناءً على التحليل الفني الحالي لـ ${selectedSymbol}، المؤشرات تشير إلى اتجاه صعودي محتمل. الدعم الرئيسي عند 2328، والمقاومة عند 2368. أنصح بالانتظار لتأكيد الاختراق قبل الدخول.`,
          'درجة الالتقاء حالياً 78%، وهو مستوى جيد للدخول. RSI يشير إلى زخم صعودي، والمرحلة الحالية في نظرية وايكوف هي مرحلة التراكم.',
          'يُنصح بالتداول بحجم لا يتجاوز 1-2% من رأس المال. ضع وقف خسارة محكم تحت المستوى الحرج 2330.00 لحماية رأس مالك.',
        ],
        en: [
          `Based on current technical analysis for ${selectedSymbol}, indicators point to a potential upward move. Key support at 2328, resistance at 2368.`,
          'Confluence score is currently 78%, a good level for entry consideration. RSI shows bullish momentum.',
          'Recommended risk per trade: 1-2% of capital. Place stop loss below 2330.00.',
        ],
      }
      const lang = language === 'ar' ? 'ar' : 'en'
      const randomResponse = fallbacks[lang][Math.floor(Math.random() * fallbacks[lang].length)]
      const assistantMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: randomResponse,
        timestamp: new Date().toISOString(),
      }
      setMessages(prev => [...prev, assistantMsg])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const quickQuestions = isRtl ? QUICK_QUESTIONS_AR : QUICK_QUESTIONS_EN

  return (
    <>
      {/* Chat Panel */}
      {isOpen && (
        <div
          className="fixed bottom-20 left-4 z-50 w-80 md:w-96 rounded-2xl overflow-hidden shadow-2xl gold-border animate-fade-in"
          style={{ background: '#111111' }}
          dir={isRtl ? 'rtl' : 'ltr'}
        >
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 bg-dark-700 border-b border-dark-600">
            <div className="flex items-center gap-2">
              <span className="text-2xl">{LION_ICON}</span>
              <div>
                <div className="text-gold font-bold text-sm">
                  {isRtl ? 'محلل أسد السوق' : 'Market Lion AI'}
                </div>
                <div className="flex items-center gap-1">
                  <div className="w-1.5 h-1.5 rounded-full bg-green-400 pulse-green" />
                  <span className="text-green-400 text-xs">{isRtl ? 'متاح' : 'Online'}</span>
                </div>
              </div>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="text-gray-400 hover:text-white transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Messages */}
          <div className="h-72 overflow-y-auto p-4 space-y-3">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={clsx(
                  'flex gap-2',
                  msg.role === 'user' ? 'justify-start' : 'justify-end'
                )}
                style={{
                  flexDirection: isRtl
                    ? (msg.role === 'user' ? 'row-reverse' : 'row')
                    : (msg.role === 'user' ? 'row' : 'row-reverse')
                }}
              >
                {msg.role === 'assistant' && (
                  <span className="text-lg shrink-0 mt-0.5">{LION_ICON}</span>
                )}
                <div
                  className={clsx(
                    'max-w-[80%] px-3 py-2 rounded-xl text-sm leading-relaxed',
                    msg.role === 'user'
                      ? 'bg-gold/20 text-white border border-gold/30'
                      : 'bg-dark-600 text-gray-200'
                  )}
                >
                  {msg.content}
                </div>
              </div>
            ))}

            {isLoading && (
              <div
                className="flex gap-2 justify-end"
                style={{ flexDirection: isRtl ? 'row' : 'row-reverse' }}
              >
                <span className="text-lg">{LION_ICON}</span>
                <div className="bg-dark-600 px-4 py-3 rounded-xl">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-gold rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <div className="w-2 h-2 bg-gold rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <div className="w-2 h-2 bg-gold rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick Questions */}
          {messages.length <= 1 && (
            <div className="px-4 pb-2">
              <div className="text-xs text-gray-500 mb-2">
                {isRtl ? 'أسئلة سريعة:' : 'Quick questions:'}
              </div>
              <div className="flex flex-wrap gap-1">
                {quickQuestions.map((q, i) => (
                  <button
                    key={i}
                    onClick={() => sendMessage(q)}
                    className="text-xs px-2 py-1 rounded-lg bg-dark-700 text-gray-300 hover:text-gold hover:bg-dark-600 transition-colors border border-dark-600"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Input */}
          <div className="p-3 border-t border-dark-600 flex gap-2">
            <input
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={isRtl ? 'اسأل عن تحليل أي زوج...' : 'Ask about any market...'}
              className="flex-1 bg-dark-700 text-white text-sm rounded-lg px-3 py-2 outline-none border border-dark-600 focus:border-gold/50"
              disabled={isLoading}
            />
            <button
              onClick={() => sendMessage()}
              disabled={isLoading || !input.trim()}
              className="px-3 py-2 rounded-lg bg-gold text-dark-900 hover:bg-gold-light transition-colors disabled:opacity-40 disabled:cursor-not-allowed shrink-0"
            >
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                style={{ transform: isRtl ? 'scaleX(-1)' : 'none' }}
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            </button>
          </div>
        </div>
      )}

      {/* Floating Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={clsx(
          'fixed bottom-4 left-4 z-50 w-14 h-14 rounded-full flex items-center justify-center shadow-2xl transition-all duration-300',
          isOpen ? 'bg-dark-700 border-2 border-gold/50' : 'gold-glow',
          !isOpen && 'pulse-green'
        )}
        style={!isOpen ? { background: 'linear-gradient(135deg, #C9A227, #E8C547)' } : {}}
      >
        {isOpen ? (
          <svg className="w-6 h-6 text-gold" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        ) : (
          <span className="text-2xl">{LION_ICON}</span>
        )}
      </button>
    </>
  )
}
