'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAppStore } from '@/lib/store'
import Header from '@/components/layout/Header'
import Sidebar from '@/components/layout/Sidebar'
import PriceTicker from '@/components/trading/PriceTicker'
import TradingChart from '@/components/trading/TradingChart'
import TraderOptionsTable from '@/components/trading/TraderOptionsTable'
import FundamentalTable from '@/components/trading/FundamentalTable'
import CoreToolsTable from '@/components/trading/CoreToolsTable'
import SchoolsTable from '@/components/trading/SchoolsTable'
import IndicatorsTable from '@/components/trading/IndicatorsTable'
import OrderFlowTable from '@/components/trading/OrderFlowTable'
import FinalDecisionsTable from '@/components/trading/FinalDecisionsTable'
import TradingPlanTable from '@/components/trading/TradingPlanTable'
import BotControl from '@/components/trading/BotControl'
import AIChat from '@/components/AIChat'
import { getAllPrices, getBotStatus, getMe } from '@/lib/api'
import { MOCK_PRICES, MOCK_BOT_STATUS } from '@/lib/mockData'

export default function DashboardPage() {
  const router = useRouter()
  const { token, setPrices, setBotStatus, setUser, sidebarOpen, language } = useAppStore()
  const [isInitialized, setIsInitialized] = useState(false)
  const isRtl = language === 'ar'

  useEffect(() => {
    const storedToken = typeof window !== 'undefined' ? localStorage.getItem('token') : null
    if (!token && !storedToken) {
      router.push('/login')
      return
    }
    setIsInitialized(true)
  }, [token, router])

  useEffect(() => {
    if (!isInitialized) return

    const initData = async () => {
      try {
        const userRes = await getMe()
        if (userRes.data) setUser(userRes.data)
      } catch {}

      try {
        const priceRes = await getAllPrices()
        if (priceRes.data) setPrices(priceRes.data)
        else setPrices(MOCK_PRICES)
      } catch {
        setPrices(MOCK_PRICES)
      }

      try {
        const botRes = await getBotStatus()
        if (botRes.data) setBotStatus(botRes.data)
        else setBotStatus(MOCK_BOT_STATUS)
      } catch {
        setBotStatus(MOCK_BOT_STATUS)
      }
    }

    initData()

    const interval = setInterval(async () => {
      try {
        const priceRes = await getAllPrices()
        if (priceRes.data) setPrices(priceRes.data)
      } catch {
        const mockWithVariance = Object.fromEntries(
          Object.entries(MOCK_PRICES).map(([key, val]) => [
            key,
            {
              ...val,
              price: val.price * (1 + (Math.random() - 0.5) * 0.001),
              change_pct: val.change_pct + (Math.random() - 0.5) * 0.05,
            }
          ])
        )
        setPrices(mockWithVariance as any)
      }
    }, 30000)

    return () => clearInterval(interval)
  }, [isInitialized, setPrices, setBotStatus, setUser])

  if (!isInitialized) {
    return (
      <div className="min-h-screen bg-dark-900 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-2 border-gold border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <div className="text-gold font-bold">{isRtl ? 'جاري التحميل...' : 'Loading...'}</div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-dark-900" dir={isRtl ? 'rtl' : 'ltr'}>
      <Header />
      <Sidebar />

      <main
        className="pt-14 transition-all duration-300"
        style={{ marginRight: isRtl && sidebarOpen ? '224px' : (!isRtl && sidebarOpen ? '224px' : '0') }}
      >
        <PriceTicker />

        <div className="p-3 space-y-3">
          {/* TradingView Chart */}
          <TradingChart />

          {/* Bot Control */}
          <BotControl />

          {/* === MARKET LION — 8 ANALYSIS TABLES IN ORDER === */}

          {/* Table 1: Trader Options — controls all tables */}
          <TraderOptionsTable />

          {/* Table 2: Fundamental Analysis — 20% weight */}
          <FundamentalTable />

          {/* Table 3: Core Tools — 30% weight */}
          <CoreToolsTable />

          {/* Table 4: Analysis Schools (48 schools) — 25% weight */}
          <SchoolsTable />

          {/* Table 5: Technical Indicators (54 indicators) — 10% weight */}
          <IndicatorsTable />

          {/* Table 6: Order Flow & BookMap — 15% weight */}
          <OrderFlowTable />

          {/* Table 7: Final Decision — weighted confluence vote */}
          <FinalDecisionsTable />

          {/* Table 8: Full Trading Plan — entry, SL, TP1-TP4, lot, leverage */}
          <TradingPlanTable />

          <div className="h-8" />
        </div>
      </main>

      <AIChat />
    </div>
  )
}
