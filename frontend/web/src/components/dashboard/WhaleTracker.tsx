'use client'
import { useState, useEffect } from 'react'

const WHALE_CATEGORIES = [
  { label: 'صغار', range: '$100–$5K', color: 'whale-small', icon: '🐟' },
  { label: 'متوسط', range: '$5K–$100K', color: 'whale-medium', icon: '🐬' },
  { label: 'كبير', range: '$100K–$500K', color: 'whale-large', icon: '🦈' },
  { label: 'كبير جداً', range: '$500K–$1M', color: 'whale-xlarge', icon: '🐳' },
  { label: 'حيتان', range: '$1M–$10M', color: 'whale-mega', icon: '🦭' },
  { label: 'حيتان كبرى', range: '$10M+', color: 'whale-king', icon: '🦁' },
]

export function WhaleTracker({ symbol }: { symbol: string }) {
  const [trades, setTrades] = useState<any[]>([])

  useEffect(() => {
    const generate = () => {
      const sides = ['BUY', 'SELL']
      const categories = [0, 1, 2, 3, 4, 5]
      const base = symbol === 'XAUUSD' ? 2350 : 78.5
      setTrades(Array.from({ length: 5 }, (_, i) => {
        const cat = categories[Math.floor(Math.random() * categories.length)]
        const sizes = [3000, 50000, 300000, 750000, 5000000, 15000000]
        return {
          id: i,
          side: sides[Math.floor(Math.random() * 2)],
          category: cat,
          size: sizes[cat] * (0.8 + Math.random() * 0.4),
          price: base + (Math.random() - 0.5) * base * 0.003,
          time: new Date(Date.now() - Math.random() * 300000).toLocaleTimeString('ar'),
        }
      }))
    }
    generate()
    const interval = setInterval(generate, 4000)
    return () => clearInterval(interval)
  }, [symbol])

  return (
    <div className="p-2 overflow-hidden">
      <div className="text-xs font-bold text-gold-500 mb-1">🦁 راصد الحيتان</div>
      <div className="space-y-0.5 overflow-hidden">
        {trades.slice(0, 4).map(trade => {
          const cat = WHALE_CATEGORIES[trade.category]
          return (
            <div key={trade.id} className="flex items-center gap-2 text-xs">
              <span>{cat.icon}</span>
              <span className={`font-bold ${trade.side === 'BUY' ? 'price-up' : 'price-down'}`}>
                {trade.side === 'BUY' ? '▲' : '▼'}
              </span>
              <span className={`font-mono ${cat.color}`}>
                ${(trade.size / 1000).toFixed(0)}K
              </span>
              <span className="text-gray-600 font-mono">{trade.price?.toFixed(2)}</span>
              <span className="text-gray-700 mr-auto">{trade.time}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
