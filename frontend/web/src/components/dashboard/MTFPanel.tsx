'use client'
import { useMemo } from 'react'

export function MTFPanel({ symbol }: { symbol: string }) {
  const tfs = ['M15', 'M30', 'H1', 'H4', 'D1']
  const dirs = useMemo(() => {
    const opts = ['BUY', 'BUY', 'BUY', 'SELL', 'NEUTRAL']
    return tfs.map(() => opts[Math.floor(Math.random() * opts.length)])
  }, [symbol])

  const aligned = dirs.filter(d => d === dirs[2]).length >= 3

  return (
    <div className="p-2 overflow-hidden">
      <div className="text-xs font-bold text-gold-500 mb-1.5">
        📊 MTF Confluence
        {aligned && <span className="mr-2 text-bull">✓ متوافق</span>}
      </div>
      <div className="flex gap-1">
        {tfs.map((tf, i) => (
          <div key={tf} className={`flex-1 rounded p-1 text-center text-xs ${
            dirs[i] === 'BUY' ? 'bg-bull/10 border border-bull/20' :
            dirs[i] === 'SELL' ? 'bg-bear/10 border border-bear/20' :
            'bg-dark-300 border border-dark-50'
          }`}>
            <div className="text-gray-600 text-xs">{tf}</div>
            <div className={`font-bold ${dirs[i] === 'BUY' ? 'price-up' : dirs[i] === 'SELL' ? 'price-down' : 'text-gray-500'}`}>
              {dirs[i] === 'BUY' ? '▲' : dirs[i] === 'SELL' ? '▼' : '—'}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
