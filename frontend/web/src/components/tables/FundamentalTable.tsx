'use client'

interface FundamentalTableProps { report: any }

const IMPACT_COLORS: Record<string, string> = {
  HIGH: 'text-red-500', MEDIUM: 'text-yellow-500', LOW: 'text-gray-500',
}

export function FundamentalTable({ report }: FundamentalTableProps) {
  if (!report) return (
    <div className="p-3 text-gray-600 text-xs text-center">جاري جلب البيانات الاقتصادية...</div>
  )

  const isBull = report.direction === 'BULL'
  const isBear = report.direction === 'BEAR'

  return (
    <div className="text-xs">
      {/* Overview */}
      <div className="flex items-center gap-2 p-2 bg-dark-300 border-b border-dark-50">
        <div className={`font-bold text-sm ${isBull ? 'price-up' : isBear ? 'price-down' : 'text-gray-500'}`}>
          {isBull ? '📈 صاعد' : isBear ? '📉 هابط' : '➡️ محايد'}
        </div>
        <div className="flex-1">
          <div className="confluence-bar">
            <div
              className={`confluence-fill ${isBull ? 'buy' : isBear ? 'sell' : ''}`}
              style={{ width: `${report.overall_score}%` }}
            />
          </div>
        </div>
        <div className={`font-mono font-bold ${isBull ? 'price-up' : isBear ? 'price-down' : 'text-gray-500'}`}>
          {report.overall_score?.toFixed(0)}%
        </div>
      </div>

      {/* News shield warning */}
      {report.news_shield_active && (
        <div className="bg-red-900/20 border-b border-red-900/30 px-2 py-1 text-red-400 font-bold text-center">
          ⚠️ خبر عالي التأثير قريب — توقف عن التداول
        </div>
      )}

      {/* Events table */}
      <div className="max-h-48 overflow-y-auto">
        <table className="data-table">
          <thead>
            <tr>
              <th className="text-right">الحدث</th>
              <th>التأثير</th>
              <th>السابق</th>
              <th>المتوقع</th>
              <th>الفعلي</th>
              <th>النتيجة</th>
            </tr>
          </thead>
          <tbody>
            {(report.events_today || []).map((event: any, i: number) => {
              const hasSurprise = event.actual != null && event.forecast != null && event.actual !== event.forecast
              const positiveSurprise = event.bias === 'BULL'
              return (
                <tr key={i}>
                  <td className="text-right max-w-24 truncate text-gray-400" title={event.title}>
                    {event.title?.slice(0, 22)}{event.title?.length > 22 ? '…' : ''}
                  </td>
                  <td className={`text-center font-bold ${IMPACT_COLORS[event.impact]}`}>
                    {event.impact === 'HIGH' ? '🔴' : event.impact === 'MEDIUM' ? '🟡' : '🟢'}
                  </td>
                  <td className="text-center text-gray-600 font-mono">{event.previous ?? '—'}</td>
                  <td className="text-center text-gray-500 font-mono">{event.forecast ?? '—'}</td>
                  <td className={`text-center font-mono font-bold ${
                    event.actual != null ? (positiveSurprise ? 'price-up' : 'price-down') : 'text-gray-600'
                  }`}>
                    {event.actual ?? '—'}
                  </td>
                  <td className={`text-center font-bold ${event.bias === 'BULL' ? 'price-up' : event.bias === 'BEAR' ? 'price-down' : 'text-gray-500'}`}>
                    {event.bias === 'BULL' ? '▲' : event.bias === 'BEAR' ? '▼' : '—'}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* Top drivers */}
      <div className="p-2 border-t border-dark-50">
        <div className="text-gray-600 mb-1">المحركات الرئيسية:</div>
        <div className="flex flex-wrap gap-1">
          {(report.top_drivers || []).slice(0, 4).map((d: string) => (
            <span key={d} className="text-xs bg-dark-300 text-gray-400 rounded px-1.5 py-0.5">{d}</span>
          ))}
        </div>
      </div>
    </div>
  )
}
