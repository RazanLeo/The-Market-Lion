'use client'
import { useState, useEffect, useCallback } from 'react'
import { TopBar } from '@/components/dashboard/TopBar'
import { ChartPanel } from '@/components/charts/ChartPanel'
import { FundamentalTable } from '@/components/tables/FundamentalTable'
import { TechnicalTable } from '@/components/tables/TechnicalTable'
import { LiquidityTable } from '@/components/tables/LiquidityTable'
import { TradePlanTable } from '@/components/tables/TradePlanTable'
import { SignalCard } from '@/components/dashboard/SignalCard'
import { PerformancePanel } from '@/components/dashboard/PerformancePanel'
import { WhaleTracker } from '@/components/dashboard/WhaleTracker'
import { MTFPanel } from '@/components/dashboard/MTFPanel'
import { BottomBar } from '@/components/dashboard/BottomBar'
import { useDashboardStore } from '@/store/dashboardStore'
import { useMarketData } from '@/hooks/useMarketData'

export default function DashboardPage() {
  const { selectedSymbol, selectedTimeframe, activeMode, setActiveMode } = useDashboardStore()
  const { signal, prices, fundamentalReport, technicalResults, isConnected } = useMarketData(selectedSymbol, selectedTimeframe)
  const [activeTab, setActiveTab] = useState<'chart' | 'analysis' | 'performance'>('chart')
  const [showRightPanel, setShowRightPanel] = useState(true)

  return (
    <div className="flex flex-col h-screen bg-dark-300 overflow-hidden" dir="rtl">
      {/* Top Bar */}
      <TopBar
        isConnected={isConnected}
        prices={prices}
        signal={signal}
        activeMode={activeMode}
        onModeChange={setActiveMode}
      />

      {/* Price Ticker */}
      <PriceTicker prices={prices} />

      <div className="flex flex-1 overflow-hidden">
        {/* Main Chart Area */}
        <div className={`flex flex-col ${showRightPanel ? 'flex-1' : 'w-full'} overflow-hidden`}>
          <ChartPanel
            symbol={selectedSymbol}
            timeframe={selectedTimeframe}
            signal={signal}
          />

          {/* Tab Navigation */}
          <div className="flex border-t border-dark-50 bg-dark-200">
            {(['chart', 'analysis', 'performance'] as const).map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-6 py-2 text-sm font-semibold transition-colors ${
                  activeTab === tab
                    ? 'text-gold-500 border-b-2 border-gold-500'
                    : 'text-gray-500 hover:text-gray-300'
                }`}
              >
                {tab === 'chart' ? '📊 شارت' : tab === 'analysis' ? '🔬 تحليل' : '📈 أداء'}
              </button>
            ))}
          </div>

          {/* Bottom info strip */}
          <BottomBar signal={signal} />
        </div>

        {/* Right Panel - 4 Tables */}
        {showRightPanel && (
          <div className="w-80 xl:w-96 border-r border-dark-50 flex flex-col overflow-y-auto bg-dark-200">
            {/* Signal Card */}
            <div className="p-3 border-b border-dark-50">
              <SignalCard signal={signal} />
            </div>

            {/* 4 Tables */}
            <div className="flex flex-col divide-y divide-dark-50 flex-1">
              <CollapsibleSection title="1️⃣ التحليل الأساسي" defaultOpen={true}>
                <FundamentalTable report={fundamentalReport} />
              </CollapsibleSection>

              <CollapsibleSection title="2️⃣ التحليل الفني" defaultOpen={true}>
                <TechnicalTable results={technicalResults} />
              </CollapsibleSection>

              <CollapsibleSection title="3️⃣ السيولة وتدفق الأموال">
                <LiquidityTable symbol={selectedSymbol} />
              </CollapsibleSection>

              <CollapsibleSection title="4️⃣ خطة التداول والمخاطرة">
                <TradePlanTable signal={signal} />
              </CollapsibleSection>
            </div>
          </div>
        )}
      </div>

      {/* Bottom Panels */}
      <div className="border-t border-dark-50 bg-dark-200 grid grid-cols-3 divide-x divide-dark-50 h-32">
        <MTFPanel symbol={selectedSymbol} />
        <WhaleTracker symbol={selectedSymbol} />
        <PerformancePanel />
      </div>
    </div>
  )
}

function PriceTicker({ prices }: { prices: Record<string, any> }) {
  const symbols = ['XAUUSD', 'USOIL', 'EURUSD', 'GBPUSD', 'USDJPY', 'BTCUSD', 'DXY']
  return (
    <div className="bg-dark-200 border-b border-dark-50 overflow-hidden h-8 flex items-center">
      <div className="flex gap-8 animate-ticker whitespace-nowrap px-4">
        {symbols.map(sym => {
          const p = prices[sym]
          const change = p?.change_pct || 0
          return (
            <span key={sym} className="text-xs font-mono flex gap-2">
              <span className="text-gold-500 font-bold">{sym}</span>
              <span className={change >= 0 ? 'price-up' : 'price-down'}>
                {p?.price?.toFixed(sym === 'USDJPY' ? 3 : sym === 'XAUUSD' ? 2 : 5) || '—'}
              </span>
              <span className={change >= 0 ? 'price-up' : 'price-down'}>
                {change >= 0 ? '▲' : '▼'}{Math.abs(change).toFixed(2)}%
              </span>
            </span>
          )
        })}
      </div>
    </div>
  )
}

function CollapsibleSection({ title, children, defaultOpen = false }: {
  title: string; children: React.ReactNode; defaultOpen?: boolean
}) {
  const [open, setOpen] = useState(defaultOpen)
  return (
    <div>
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-3 py-2 text-xs font-bold text-gold-500 hover:bg-dark-50/50 transition-colors"
      >
        <span>{title}</span>
        <span className="text-gray-500">{open ? '▲' : '▼'}</span>
      </button>
      {open && <div className="overflow-hidden">{children}</div>}
    </div>
  )
}
