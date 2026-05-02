'use client'
import { useState } from 'react'
import { LionLogo } from '@/components/ui/LionLogo'
import { useDashboardStore } from '@/store/dashboardStore'

const SYMBOLS = ['XAUUSD', 'USOIL', 'XBRUSD', 'EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD', 'USDCHF', 'NZDUSD', 'BTCUSD', 'ETHUSD']
const TIMEFRAMES = ['M1', 'M5', 'M15', 'M30', 'H1', 'H4', 'D1', 'W1', 'MN']
const SYMBOL_NAMES: Record<string, string> = {
  XAUUSD: 'الذهب', USOIL: 'النفط WTI', EURUSD: 'يورو/دولار',
  GBPUSD: 'جنيه/دولار', USDJPY: 'دولار/ين', XBRUSD: 'برنت',
  AUDUSD: 'أسترالي', USDCAD: 'كندي', USDCHF: 'فرنك', BTCUSD: 'بيتكوين',
}

interface TopBarProps {
  isConnected: boolean
  prices: Record<string, any>
  signal: any
  activeMode: string
  onModeChange: (mode: any) => void
}

export function TopBar({ isConnected, prices, signal, activeMode, onModeChange }: TopBarProps) {
  const { selectedSymbol, selectedTimeframe, setSelectedSymbol, setSelectedTimeframe } = useDashboardStore()
  const [showSymbolPicker, setShowSymbolPicker] = useState(false)
  const currentPrice = prices[selectedSymbol]

  return (
    <div className="h-14 bg-dark-200 border-b border-dark-50 flex items-center gap-3 px-4 shrink-0">
      {/* Logo */}
      <div className="flex items-center gap-2 ml-2">
        <LionLogo size={36} />
        <div className="hidden md:flex flex-col">
          <span className="text-gold-500 font-black text-sm leading-none">أسد السوق</span>
          <span className="text-gray-600 text-xs">The Market Lion</span>
        </div>
      </div>

      <div className="w-px h-8 bg-dark-50 mx-1" />

      {/* Symbol Selector */}
      <div className="relative">
        <button
          onClick={() => setShowSymbolPicker(!showSymbolPicker)}
          className="flex items-center gap-2 bg-dark-100 hover:bg-dark-50 border border-dark-50 rounded-lg px-3 py-1.5 transition-colors"
        >
          <span className="text-gold-500 font-bold text-sm">{selectedSymbol}</span>
          <span className="text-gray-500 text-xs hidden md:inline">{SYMBOL_NAMES[selectedSymbol] || ''}</span>
          <span className="text-gray-600 text-xs">▼</span>
        </button>
        {showSymbolPicker && (
          <div className="absolute top-full mt-1 right-0 bg-dark-100 border border-dark-50 rounded-xl shadow-2xl z-50 p-2 w-48">
            {SYMBOLS.map(sym => (
              <button
                key={sym}
                onClick={() => { setSelectedSymbol(sym); setShowSymbolPicker(false) }}
                className={`w-full text-right px-3 py-2 rounded-lg text-sm transition-colors flex justify-between ${
                  sym === selectedSymbol ? 'bg-gold-500/20 text-gold-500' : 'hover:bg-dark-50 text-gray-300'
                }`}
              >
                <span className="text-gray-500 text-xs">{SYMBOL_NAMES[sym] || sym}</span>
                <span className="font-bold">{sym}</span>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Current Price */}
      {currentPrice && (
        <div className="flex items-baseline gap-1">
          <span className={`text-lg font-mono font-bold ${currentPrice.change_pct >= 0 ? 'price-up' : 'price-down'}`}>
            {currentPrice.price?.toFixed(selectedSymbol === 'USDJPY' ? 3 : selectedSymbol === 'XAUUSD' ? 2 : 5)}
          </span>
          <span className={`text-xs ${currentPrice.change_pct >= 0 ? 'price-up' : 'price-down'}`}>
            {currentPrice.change_pct >= 0 ? '+' : ''}{currentPrice.change_pct?.toFixed(3)}%
          </span>
        </div>
      )}

      {/* Timeframe */}
      <div className="flex gap-1 bg-dark-100 rounded-lg p-1">
        {TIMEFRAMES.map(tf => (
          <button
            key={tf}
            onClick={() => setSelectedTimeframe(tf)}
            className={`px-2 py-0.5 rounded-md text-xs font-semibold transition-all ${
              tf === selectedTimeframe
                ? 'bg-gold-500 text-dark-300'
                : 'text-gray-500 hover:text-gray-300'
            }`}
          >
            {tf}
          </button>
        ))}
      </div>

      <div className="flex-1" />

      {/* Signal Badge */}
      {signal && (
        <div className={signal.side === 'BUY' ? 'badge-buy' : signal.side === 'SELL' ? 'badge-sell' : 'badge-neutral'}>
          {signal.side === 'BUY' ? '🟢 شراء' : signal.side === 'SELL' ? '🔴 بيع' : '⚪ محايد'}
          {' '}{signal.confluenceScore?.toFixed(0)}%
        </div>
      )}

      {/* Trading Mode */}
      <div className="flex gap-1 bg-dark-100 rounded-lg p-1">
        {[
          { key: 'auto', label: '⚡ آلي' },
          { key: 'semi-auto', label: '🔔 شبه آلي' },
          { key: 'manual', label: '✋ يدوي' },
        ].map(({ key, label }) => (
          <button
            key={key}
            onClick={() => onModeChange(key)}
            className={`px-2 py-0.5 rounded-md text-xs font-semibold transition-all whitespace-nowrap ${
              activeMode === key ? 'bg-gold-500/20 text-gold-500 border border-gold-500/40' : 'text-gray-500 hover:text-gray-300'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Connection Status */}
      <div className={`flex items-center gap-1.5 text-xs ${isConnected ? 'text-bull' : 'text-gray-600'}`}>
        <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-bull animate-pulse' : 'bg-gray-600'}`} />
        <span className="hidden md:inline">{isConnected ? 'متصل' : 'تجريبي'}</span>
      </div>
    </div>
  )
}
