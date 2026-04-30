'use client'

interface TechnicalTableProps { results: any[] }

const TF_COLORS: Record<string, string> = {
  BUY: 'price-up', SELL: 'price-down', NEUTRAL: 'text-gray-500',
}

export function TechnicalTable({ results }: TechnicalTableProps) {
  if (!results || results.length === 0) return (
    <div className="p-3 text-gray-600 text-xs text-center">جاري حساب المؤشرات...</div>
  )

  const buys = results.filter(r => r.vote === 'BUY').length
  const sells = results.filter(r => r.vote === 'SELL').length
  const neutrals = results.filter(r => r.vote === 'NEUTRAL').length
  const total = results.length
  const buyPct = Math.round((buys / total) * 100)
  const sellPct = Math.round((sells / total) * 100)

  return (
    <div className="text-xs">
      {/* Summary row */}
      <div className="flex gap-2 p-2 bg-dark-300 border-b border-dark-50">
        <div className="flex-1 text-center">
          <div className="price-up font-bold text-sm">{buys}</div>
          <div className="text-gray-600">شراء ({buyPct}%)</div>
        </div>
        <div className="flex-1 text-center">
          <div className="price-down font-bold text-sm">{sells}</div>
          <div className="text-gray-600">بيع ({sellPct}%)</div>
        </div>
        <div className="flex-1 text-center">
          <div className="text-gray-500 font-bold text-sm">{neutrals}</div>
          <div className="text-gray-600">محايد</div>
        </div>
      </div>

      {/* Overall bar */}
      <div className="px-2 py-1 border-b border-dark-50">
        <div className="h-2 bg-dark-300 rounded-full overflow-hidden flex">
          <div className="bg-bull" style={{ width: `${buyPct}%` }} />
          <div className="bg-dark-50 flex-1" />
          <div className="bg-bear" style={{ width: `${sellPct}%` }} />
        </div>
      </div>

      {/* School results table */}
      <div className="max-h-64 overflow-y-auto">
        <table className="data-table">
          <thead>
            <tr>
              <th className="text-right">المدرسة</th>
              <th>H1</th>
              <th>H4</th>
              <th>D1</th>
            </tr>
          </thead>
          <tbody>
            {results.map((r) => (
              <tr key={r.school}>
                <td className="text-right text-gray-400">
                  <div className="flex items-center justify-end gap-1">
                    <span>{r.school}</span>
                    <span className={`w-1.5 h-1.5 rounded-full ${r.vote === 'BUY' ? 'bg-bull' : r.vote === 'SELL' ? 'bg-bear' : 'bg-gray-600'}`} />
                  </div>
                </td>
                {(['H1', 'H4', 'D1'] as const).map(tf => (
                  <td key={tf} className={`text-center font-bold ${TF_COLORS[r.timeframes?.[tf] || r.vote]}`}>
                    {r.timeframes?.[tf] === 'BUY' ? '▲' : r.timeframes?.[tf] === 'SELL' ? '▼' : '—'}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* 5 TF summary */}
      <div className="grid grid-cols-5 border-t border-dark-50 text-center">
        {(['M15', 'M30', 'H1', 'H4', 'D1'] as const).map(tf => {
          const tfVotes = results.map(r => r.timeframes?.[tf] || r.vote)
          const tfBuy = tfVotes.filter(v => v === 'BUY').length
          const tfSell = tfVotes.filter(v => v === 'SELL').length
          const tfPct = tfBuy > tfSell ? Math.round(tfBuy / tfVotes.length * 100) : Math.round(tfSell / tfVotes.length * 100)
          const dir = tfBuy > tfSell ? 'BUY' : tfSell > tfBuy ? 'SELL' : 'NEUTRAL'
          return (
            <div key={tf} className={`py-1.5 border-r last:border-r-0 border-dark-50 ${dir === 'BUY' ? 'bg-bull/10' : dir === 'SELL' ? 'bg-bear/10' : ''}`}>
              <div className="text-gray-600 text-xs">{tf}</div>
              <div className={`font-bold text-sm ${TF_COLORS[dir]}`}>{tfPct}%</div>
              <div className={`text-xs ${TF_COLORS[dir]}`}>{dir === 'BUY' ? 'شراء' : dir === 'SELL' ? 'بيع' : 'محايد'}</div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
