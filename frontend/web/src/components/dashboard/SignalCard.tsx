'use client'

interface SignalCardProps { signal: any }

export function SignalCard({ signal }: SignalCardProps) {
  if (!signal) return (
    <div className="card-dark p-3 text-center text-gray-600 text-sm">جاري التحليل...</div>
  )

  const isBuy = signal.side === 'BUY'
  const isSell = signal.side === 'SELL'

  return (
    <div className={`signal-card ${isBuy ? 'buy' : isSell ? 'sell' : ''}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs text-gray-500">🦁 إشارة أسد السوق</span>
        <span className={isBuy ? 'badge-buy' : isSell ? 'badge-sell' : 'badge-neutral'}>
          {isBuy ? '🟢 شراء' : isSell ? '🔴 بيع' : '⚪ محايد'}
        </span>
      </div>

      {/* Confluence Score */}
      <div className="mb-3">
        <div className="flex justify-between text-xs mb-1">
          <span className="text-gray-500">درجة التوافق</span>
          <span className={`font-bold font-mono ${signal.confluenceScore >= 75 ? 'price-up' : signal.confluenceScore >= 60 ? 'text-gold-500' : 'price-down'}`}>
            {signal.confluenceScore?.toFixed(1)}%
          </span>
        </div>
        <div className="confluence-bar">
          <div
            className={`confluence-fill ${isBuy ? 'buy' : isSell ? 'sell' : ''}`}
            style={{ width: `${Math.min(100, signal.confluenceScore)}%` }}
          />
        </div>
        <div className="flex justify-between text-xs mt-0.5 text-gray-700">
          <span>0%</span>
          <span className="text-gray-600">عتبة الدخول: 75%</span>
          <span>100%</span>
        </div>
      </div>

      {/* Trade levels */}
      <div className="grid grid-cols-2 gap-1 text-xs">
        <div className="bg-dark-300 rounded-lg p-2">
          <div className="text-gray-600 mb-0.5">دخول</div>
          <div className="font-mono font-bold text-gold-500">{signal.entry?.toFixed(5)}</div>
        </div>
        <div className="bg-dark-300 rounded-lg p-2">
          <div className="text-gray-600 mb-0.5">وقف الخسارة</div>
          <div className="font-mono font-bold price-down">{signal.sl?.toFixed(5)}</div>
        </div>
        <div className="bg-dark-300 rounded-lg p-2">
          <div className="text-gray-600 mb-0.5">هدف 1 (1:1)</div>
          <div className="font-mono font-bold price-up">{signal.tp1?.toFixed(5)}</div>
        </div>
        <div className="bg-dark-300 rounded-lg p-2">
          <div className="text-gray-600 mb-0.5">هدف 2 (1:2)</div>
          <div className="font-mono font-bold price-up">{signal.tp2?.toFixed(5)}</div>
        </div>
      </div>

      <div className="bg-dark-300 rounded-lg p-2 mt-1 text-xs">
        <div className="text-gray-600 mb-0.5">هدف 3 (1:{signal.rr3?.toFixed(1)})</div>
        <div className="font-mono font-bold price-up text-sm">{signal.tp3?.toFixed(5)}</div>
      </div>

      {/* Risk info */}
      <div className="flex gap-2 mt-2 text-xs">
        <div className="flex-1 bg-dark-300 rounded p-1.5 text-center">
          <div className="text-gray-600">حجم اللوت</div>
          <div className="font-mono font-bold text-gold-500">{signal.lotSize}</div>
        </div>
        <div className="flex-1 bg-dark-300 rounded p-1.5 text-center">
          <div className="text-gray-600">المخاطرة</div>
          <div className="font-mono font-bold text-gold-500">{signal.riskPct}%</div>
        </div>
        <div className="flex-1 bg-dark-300 rounded p-1.5 text-center">
          <div className="text-gray-600">ريشيو</div>
          <div className="font-mono font-bold price-up">1:{signal.rr3?.toFixed(0)}</div>
        </div>
      </div>

      {/* Should trade indicator */}
      <div className={`mt-2 rounded-lg p-2 text-center text-xs font-bold ${
        signal.shouldTrade
          ? 'bg-bull/15 text-bull border border-bull/30'
          : 'bg-dark-300 text-gray-600 border border-dark-50'
      }`}>
        {signal.shouldTrade
          ? '✅ شروط الدخول مكتملة — جاهز للتنفيذ'
          : `⏳ انتظر — ${signal.rejectionReasons?.[0] || 'التوافق أقل من 75%'}`}
      </div>

      {/* Top factors */}
      {signal.topFactors?.length > 0 && (
        <div className="mt-2">
          <div className="text-xs text-gray-600 mb-1">أقوى العوامل:</div>
          <div className="flex flex-wrap gap-1">
            {signal.topFactors.slice(0, 3).map((f: string) => (
              <span key={f} className="text-xs bg-gold-500/10 text-gold-500 rounded px-2 py-0.5 border border-gold-500/20">
                {f}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
