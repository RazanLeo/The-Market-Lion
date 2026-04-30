'use client'

interface TradePlanTableProps { signal: any }

export function TradePlanTable({ signal }: TradePlanTableProps) {
  if (!signal) return <div className="p-3 text-gray-600 text-xs text-center">انتظار الإشارة...</div>

  const rows = [
    { label: 'نوع الصفقة', value: 'CFD — مضاربة' },
    { label: 'نقطة الدخول', value: signal.entry?.toFixed(5), color: 'text-gold-500' },
    { label: 'وقف الخسارة', value: signal.sl?.toFixed(5), color: 'price-down' },
    { label: 'هدف 1 (TP1)', value: signal.tp1?.toFixed(5), color: 'price-up' },
    { label: 'هدف 2 (TP2)', value: signal.tp2?.toFixed(5), color: 'price-up' },
    { label: 'هدف 3 (TP3)', value: signal.tp3?.toFixed(5), color: 'price-up' },
    { label: 'ريشيو TP1', value: `1:${signal.rr1?.toFixed(1)}` },
    { label: 'ريشيو TP2', value: `1:${signal.rr2?.toFixed(1)}` },
    { label: 'ريشيو TP3', value: `1:${signal.rr3?.toFixed(1)}` },
    { label: 'حجم اللوت', value: signal.lotSize?.toFixed(2), color: 'text-gold-500' },
    { label: 'نسبة المخاطرة', value: `${signal.riskPct?.toFixed(1)}%`, color: 'text-gold-500' },
    { label: 'درجة التوافق', value: `${signal.confluenceScore?.toFixed(1)}%`, color: signal.confluenceScore >= 75 ? 'price-up' : 'price-down' },
    { label: 'التحليل الأساسي', value: `${signal.fundamentalScore?.toFixed(0)}%` },
    { label: 'التحليل الفني', value: `${signal.technicalScore?.toFixed(0)}%` },
  ]

  return (
    <div className="text-xs">
      <table className="data-table w-full">
        <tbody>
          {rows.map(({ label, value, color }) => (
            <tr key={label}>
              <td className="text-gray-500 text-right py-1.5 px-2">{label}</td>
              <td className={`font-mono font-bold py-1.5 px-2 text-left ${color || 'text-gray-300'}`}>{value}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Actions */}
      <div className="p-2 flex gap-2">
        <button className="flex-1 btn-gold text-xs py-2 rounded-lg">
          {signal.side === 'BUY' ? '🟢 تنفيذ شراء' : '🔴 تنفيذ بيع'}
        </button>
        <button className="flex-1 btn-outline-gold text-xs py-2 rounded-lg">
          🔔 تنبيه فقط
        </button>
      </div>

      {/* School breakdown mini */}
      <div className="p-2 border-t border-dark-50">
        <div className="text-gray-600 mb-1">المدارس الموافقة:</div>
        <div className="flex flex-wrap gap-1">
          {(signal.schoolBreakdown || [])
            .filter((s: any) => s.vote === signal.side)
            .slice(0, 6)
            .map((s: any) => (
              <span key={s.school} className="text-xs bg-bull/10 text-bull rounded px-1.5 py-0.5 border border-bull/20">
                {s.school}
              </span>
            ))}
        </div>
      </div>
    </div>
  )
}
