'use client'

import { useState } from 'react'
import { startBot, stopBot } from '@/lib/api'
import { useAppStore } from '@/lib/store'
import { SYMBOLS } from '@/lib/mockData'
import toast from 'react-hot-toast'
import clsx from 'clsx'

export default function BotControl() {
  const { botStatus, setBotStatus, language } = useAppStore()
  const [isLoading, setIsLoading] = useState(false)
  const [selectedSymbols, setSelectedSymbols] = useState<string[]>(botStatus.active_symbols)
  const [mode, setMode] = useState<'auto' | 'semi-auto' | 'manual'>(botStatus.mode)
  const isRtl = language === 'ar'

  const handleToggleBot = async () => {
    setIsLoading(true)
    try {
      if (botStatus.is_running) {
        await stopBot()
        setBotStatus({ ...botStatus, is_running: false, started_at: null })
        toast.success(isRtl ? 'تم إيقاف الروبوت' : 'Bot stopped')
      } else {
        if (selectedSymbols.length === 0) {
          toast.error(isRtl ? 'اختر زوجاً واحداً على الأقل' : 'Select at least one symbol')
          return
        }
        await startBot({ mode, symbols: selectedSymbols })
        setBotStatus({
          ...botStatus,
          is_running: true,
          mode,
          active_symbols: selectedSymbols,
          started_at: new Date().toISOString(),
        })
        toast.success(isRtl ? 'تم تشغيل الروبوت! 🦁' : 'Bot started! 🦁')
      }
    } catch {
      // Simulate for demo
      if (botStatus.is_running) {
        setBotStatus({ ...botStatus, is_running: false, started_at: null })
        toast.success(isRtl ? 'تم إيقاف الروبوت' : 'Bot stopped')
      } else {
        setBotStatus({
          ...botStatus,
          is_running: true,
          mode,
          active_symbols: selectedSymbols,
          started_at: new Date().toISOString(),
        })
        toast.success(isRtl ? 'تم تشغيل الروبوت! 🦁' : 'Bot started! 🦁')
      }
    } finally {
      setIsLoading(false)
    }
  }

  const toggleSymbol = (sym: string) => {
    setSelectedSymbols(prev =>
      prev.includes(sym) ? prev.filter(s => s !== sym) : [...prev, sym]
    )
  }

  const modeOptions = [
    { value: 'auto', label: isRtl ? 'تلقائي' : 'Auto', desc: isRtl ? 'ينفذ الصفقات تلقائياً' : 'Executes trades automatically' },
    { value: 'semi-auto', label: isRtl ? 'شبه تلقائي' : 'Semi-Auto', desc: isRtl ? 'يقترح وأنت تؤكد' : 'Suggests, you confirm' },
    { value: 'manual', label: isRtl ? 'يدوي' : 'Manual', desc: isRtl ? 'إشارات فقط' : 'Signals only' },
  ]

  const uptime = botStatus.started_at ? (() => {
    const mins = Math.floor((Date.now() - new Date(botStatus.started_at).getTime()) / 60000)
    if (mins < 60) return `${mins}${isRtl ? 'د' : 'm'}`
    return `${Math.floor(mins / 60)}${isRtl ? 'س' : 'h'} ${mins % 60}${isRtl ? 'د' : 'm'}`
  })() : null

  return (
    <div className="bg-dark-800 rounded-xl gold-border p-4">
      <div className="flex items-center gap-2 mb-4">
        <span className="text-lg">🤖</span>
        <h3 className="text-gold font-bold text-sm">
          {isRtl ? 'التحكم بالروبوت' : 'Bot Control'}
        </h3>
        {botStatus.is_running && uptime && (
          <span className="text-xs text-gray-500 mr-auto">
            {isRtl ? 'وقت التشغيل:' : 'Uptime:'} {uptime}
          </span>
        )}
      </div>

      {/* Mode Selector */}
      <div className="mb-4">
        <label className="text-xs text-gray-400 mb-2 block">
          {isRtl ? 'وضع التداول:' : 'Trading Mode:'}
        </label>
        <div className="grid grid-cols-3 gap-1">
          {modeOptions.map(opt => (
            <button
              key={opt.value}
              onClick={() => !botStatus.is_running && setMode(opt.value as any)}
              disabled={botStatus.is_running}
              className={clsx(
                'px-2 py-2 rounded-lg text-xs font-medium transition-all',
                mode === opt.value
                  ? 'bg-gold text-dark-900 font-bold'
                  : 'bg-dark-700 text-gray-400 hover:text-white hover:bg-dark-600',
                botStatus.is_running && 'cursor-not-allowed opacity-60'
              )}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {/* Symbol Selection */}
      <div className="mb-4">
        <label className="text-xs text-gray-400 mb-2 block">
          {isRtl ? 'الأزواج النشطة:' : 'Active Symbols:'}
        </label>
        <div className="flex flex-wrap gap-1.5">
          {SYMBOLS.slice(0, 5).map(sym => (
            <button
              key={sym.value}
              onClick={() => !botStatus.is_running && toggleSymbol(sym.value)}
              disabled={botStatus.is_running}
              className={clsx(
                'px-2 py-1 rounded text-xs font-medium transition-all border',
                selectedSymbols.includes(sym.value)
                  ? 'bg-gold/20 text-gold border-gold/50'
                  : 'bg-dark-700 text-gray-400 border-dark-600',
                botStatus.is_running && 'cursor-not-allowed opacity-60'
              )}
            >
              {isRtl ? sym.labelAr : sym.label}
            </button>
          ))}
        </div>
      </div>

      {/* Stats when running */}
      {botStatus.is_running && (
        <div className="grid grid-cols-2 gap-2 mb-4">
          <div className="bg-dark-700 rounded-lg p-2 text-center">
            <div className="text-xs text-gray-400">{isRtl ? 'إشارات اليوم' : 'Signals Today'}</div>
            <div className="text-gold font-bold">{botStatus.total_signals_today}</div>
          </div>
          <div className="bg-dark-700 rounded-lg p-2 text-center">
            <div className="text-xs text-gray-400">{isRtl ? 'صفقات اليوم' : 'Trades Today'}</div>
            <div className="text-white font-bold">{botStatus.total_trades_today}</div>
          </div>
        </div>
      )}

      {/* Start/Stop Button */}
      <button
        onClick={handleToggleBot}
        disabled={isLoading}
        className={clsx(
          'w-full py-3 rounded-xl font-bold text-sm transition-all duration-300 flex items-center justify-center gap-2',
          botStatus.is_running
            ? 'bg-sell text-white hover:bg-red-700 pulse-green'
            : 'btn-green',
          isLoading && 'opacity-50 cursor-not-allowed'
        )}
      >
        {isLoading ? (
          <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        ) : (
          <>
            <span>{botStatus.is_running ? '⏹' : '▶'}</span>
            {botStatus.is_running
              ? (isRtl ? 'إيقاف الروبوت' : 'Stop Bot')
              : (isRtl ? 'تشغيل الروبوت' : 'Start Bot')}
          </>
        )}
      </button>
    </div>
  )
}
