'use client'

export function PerformancePanel() {
  const stats = {
    winRate: 78.4, totalPL: 3840, dailyPL: 420, weeklyPL: 1280,
    sharpe: 2.8, maxDD: 8.2, trades: 47, profitFactor: 3.2,
  }
  return (
    <div className="p-2 overflow-hidden">
      <div className="text-xs font-bold text-gold-500 mb-1.5">📈 الأداء</div>
      <div className="grid grid-cols-4 gap-1 text-xs text-center">
        <div>
          <div className="text-gray-600">Win Rate</div>
          <div className="font-bold price-up">{stats.winRate}%</div>
        </div>
        <div>
          <div className="text-gray-600">P/L يومي</div>
          <div className="font-bold price-up">+${stats.dailyPL}</div>
        </div>
        <div>
          <div className="text-gray-600">Sharpe</div>
          <div className="font-bold text-gold-500">{stats.sharpe}</div>
        </div>
        <div>
          <div className="text-gray-600">Max DD</div>
          <div className="font-bold price-down">{stats.maxDD}%</div>
        </div>
      </div>
    </div>
  )
}
