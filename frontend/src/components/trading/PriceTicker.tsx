'use client'

import { useEffect, useState } from 'react'
import { useAppStore } from '@/lib/store'
import { getAllPrices } from '@/lib/api'
import { MOCK_PRICES } from '@/lib/mockData'
import type { PriceData } from '@/types'
import clsx from 'clsx'

const TICKER_SYMBOLS = ['XAUUSD', 'XAGUSD', 'WTI', 'BRENT', 'EURUSD', 'GBPUSD', 'BTCUSD', 'DXY']

function TickerItem({ data }: { data: PriceData }) {
  const isPositive = data.change_pct >= 0
  const isForex = data.symbol.includes('/') && !data.symbol.includes('BTC') && !data.symbol.includes('XAU') && !data.symbol.includes('XAG')
  const decimals = isForex ? 4 : data.symbol.includes('BTC') ? 0 : 2

  return (
    <div className="flex items-center gap-3 px-4 shrink-0">
      <span className="text-gray-300 text-xs font-medium whitespace-nowrap">{data.symbol}</span>
      <span className="text-white text-xs font-bold">{data.price.toFixed(decimals)}</span>
      <span className={clsx('text-xs font-semibold whitespace-nowrap', isPositive ? 'text-green-400' : 'text-red-400')}>
        {isPositive ? '▲' : '▼'} {Math.abs(data.change_pct).toFixed(2)}%
      </span>
      <span className="text-dark-600 text-xs">|</span>
    </div>
  )
}

export default function PriceTicker() {
  const { prices, setPrices } = useAppStore()
  const [tickerData, setTickerData] = useState<PriceData[]>([])

  useEffect(() => {
    // Load initial mock data
    const initial = TICKER_SYMBOLS.map(s => MOCK_PRICES[s]).filter(Boolean)
    setTickerData(initial)
    setPrices(MOCK_PRICES)

    // Fetch from API
    const fetchPrices = async () => {
      try {
        const res = await getAllPrices()
        if (res.data) {
          setPrices(res.data)
          const updated = TICKER_SYMBOLS.map(s => res.data[s]).filter(Boolean)
          setTickerData(updated)
        }
      } catch {
        // Use mock data on error
        const withVariance = TICKER_SYMBOLS.map(s => {
          const base = MOCK_PRICES[s]
          if (!base) return null
          const variance = (Math.random() - 0.5) * 0.001
          return {
            ...base,
            price: base.price * (1 + variance),
            change_pct: base.change_pct + (Math.random() - 0.5) * 0.1,
          }
        }).filter(Boolean) as PriceData[]
        setTickerData(withVariance)
      }
    }

    fetchPrices()
    const interval = setInterval(fetchPrices, 5000)
    return () => clearInterval(interval)
  }, [setPrices])

  if (tickerData.length === 0) return null

  // Duplicate for seamless loop
  const doubled = [...tickerData, ...tickerData]

  return (
    <div className="h-8 bg-dark-700 border-b border-dark-600 overflow-hidden relative">
      {/* Gradient masks */}
      <div className="absolute left-0 top-0 bottom-0 w-8 z-10"
        style={{ background: 'linear-gradient(to right, #1A1A1A, transparent)' }} />
      <div className="absolute right-0 top-0 bottom-0 w-8 z-10"
        style={{ background: 'linear-gradient(to left, #1A1A1A, transparent)' }} />

      <div
        className="flex items-center h-full"
        style={{
          animation: 'ticker 40s linear infinite',
          width: 'max-content',
        }}
      >
        {doubled.map((item, i) => (
          <TickerItem key={i} data={item} />
        ))}
      </div>
    </div>
  )
}
