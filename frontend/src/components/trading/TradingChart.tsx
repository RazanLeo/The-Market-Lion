'use client'

import { useEffect, useRef, useState } from 'react'
import { useAppStore } from '@/lib/store'
import { SYMBOLS, TIMEFRAMES } from '@/lib/mockData'

const SYMBOL_MAP: Record<string, string> = {
  XAUUSD: 'OANDA:XAUUSD',
  XAGUSD: 'OANDA:XAGUSD',
  WTI: 'TVC:USOIL',
  BRENT: 'TVC:UKOIL',
  EURUSD: 'EURUSD',
  GBPUSD: 'GBPUSD',
  BTCUSD: 'BINANCE:BTCUSDT',
  DXY: 'TVC:DXY',
}

const INTERVAL_MAP: Record<string, string> = {
  M1: '1',
  M5: '5',
  M15: '15',
  M30: '30',
  H1: '60',
  H4: '240',
  D1: 'D',
  W1: 'W',
}

export default function TradingChart() {
  const { selectedSymbol, selectedTimeframe, setTimeframe, language } = useAppStore()
  const containerRef = useRef<HTMLDivElement>(null)
  const [isLoaded, setIsLoaded] = useState(false)
  const isRtl = language === 'ar'

  const tvSymbol = SYMBOL_MAP[selectedSymbol] || 'OANDA:XAUUSD'
  const tvInterval = INTERVAL_MAP[selectedTimeframe] || '60'

  const chartUrl = `https://www.tradingview.com/widgetembed/?frameElementId=tradingview_chart&symbol=${encodeURIComponent(tvSymbol)}&interval=${tvInterval}&hidesidetoolbar=0&symboledit=1&saveimage=1&toolbarbg=111111&studies=[]&theme=dark&style=1&timezone=Asia%2FRiyadh&withdateranges=1&showpopupbutton=1&studies_overrides={"paneProperties.background"%3A"%230A0A0A"%2C"paneProperties.vertGridProperties.color"%3A"%231A1A1A"%2C"paneProperties.horzGridProperties.color"%3A"%231A1A1A"}&overrides={"editorFontsList"%3A["Cairo"%2C"Inter"]}&enabled_features=[]&disabled_features=["header_symbol_search"]&locale=ar&utm_source=market-lion&utm_medium=widget`

  useEffect(() => {
    setIsLoaded(false)
    const timer = setTimeout(() => setIsLoaded(true), 100)
    return () => clearTimeout(timer)
  }, [selectedSymbol, selectedTimeframe])

  return (
    <div className="bg-dark-800 rounded-xl overflow-hidden gold-border flex flex-col" style={{ height: '460px' }}>
      {/* Chart Header */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-dark-700 bg-dark-800 shrink-0">
        <div className="flex items-center gap-3">
          <span className="text-gold font-bold text-sm">
            {isRtl
              ? SYMBOLS.find(s => s.value === selectedSymbol)?.labelAr
              : SYMBOLS.find(s => s.value === selectedSymbol)?.label}
          </span>
          <span className="text-gray-500 text-xs">TradingView</span>
        </div>

        {/* Timeframe Selector */}
        <div className="flex items-center gap-1">
          {TIMEFRAMES.map(tf => (
            <button
              key={tf.value}
              onClick={() => setTimeframe(tf.value)}
              className={`px-2 py-0.5 text-xs rounded transition-colors ${
                selectedTimeframe === tf.value
                  ? 'bg-gold text-dark-900 font-bold'
                  : 'text-gray-400 hover:text-white hover:bg-dark-700'
              }`}
            >
              {isRtl ? tf.labelAr : tf.label}
            </button>
          ))}
        </div>
      </div>

      {/* TradingView Chart */}
      <div ref={containerRef} className="flex-1 relative bg-dark-900">
        {!isLoaded && (
          <div className="absolute inset-0 flex items-center justify-center bg-dark-900">
            <div className="text-center">
              <div className="w-12 h-12 border-2 border-gold border-t-transparent rounded-full animate-spin mx-auto mb-3" />
              <div className="text-gray-400 text-sm">{isRtl ? 'جاري تحميل الرسم البياني...' : 'Loading chart...'}</div>
            </div>
          </div>
        )}
        <iframe
          key={`${selectedSymbol}-${selectedTimeframe}`}
          src={chartUrl}
          className="w-full h-full border-0"
          allowTransparency={true}
          scrolling="no"
          allowFullScreen={true}
          onLoad={() => setIsLoaded(true)}
          style={{ display: isLoaded ? 'block' : 'none' }}
        />
      </div>
    </div>
  )
}
