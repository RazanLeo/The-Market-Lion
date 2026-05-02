'use client'

export function BottomBar({ signal }: { signal: any }) {
  if (!signal) return null
  return (
    <div className="h-8 bg-dark-300 border-t border-dark-50 flex items-center gap-4 px-3 text-xs">
      <span className="text-gray-600">أسد السوق v2.0</span>
      <span className="text-dark-50">|</span>
      {signal && (
        <>
          <span className="text-gray-500">
            إشارة: <span className={signal.side === 'BUY' ? 'price-up' : signal.side === 'SELL' ? 'price-down' : 'text-gray-500'}>
              {signal.side}
            </span>
          </span>
          <span className="text-gray-500">
            توافق: <span className={`font-bold ${signal.confluenceScore >= 75 ? 'price-up' : 'text-gold-500'}`}>
              {signal.confluenceScore?.toFixed(1)}%
            </span>
          </span>
          <span className="text-gray-500">دخول: <span className="font-mono text-gold-500">{signal.entry?.toFixed(5)}</span></span>
          <span className="text-gray-500">SL: <span className="font-mono price-down">{signal.sl?.toFixed(5)}</span></span>
          <span className="text-gray-500">TP3: <span className="font-mono price-up">{signal.tp3?.toFixed(5)}</span></span>
        </>
      )}
      <span className="mr-auto text-gray-700 font-mono">{new Date().toLocaleTimeString('ar')}</span>
    </div>
  )
}
