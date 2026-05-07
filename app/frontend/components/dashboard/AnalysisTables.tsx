'use client';
import { useEffect, useState } from 'react';
import { useTranslations } from 'next-intl';
import { api } from '@/lib/api';

type Row = { code: string; result: 'buy'|'sell'|'neutral'; confidence: number; weight: number; payload: any };

export function AnalysisTables({ symbol, tf }: { symbol: string; tf: string }) {
  const t = useTranslations('dashboard');
  const t2 = useTranslations('table');
  const [schools, setSchools] = useState<Row[]>([]);
  const [indicators, setIndicators] = useState<Row[]>([]);
  const [confluence, setConfluence] = useState<any | null>(null);
  const [news, setNews] = useState<any[]>([]);

  useEffect(() => {
    let alive = true;
    async function pull() {
      try {
        const [s, i, c, f] = await Promise.all([
          api.get(`/analysis/schools?symbol=${symbol}&tf=${tf}`),
          api.get(`/analysis/indicators?symbol=${symbol}&tf=${tf}`),
          api.get(`/analysis/confluence?symbol=${symbol}&tf=${tf}`),
          api.get(`/analysis/fundamental?symbol=${symbol}&tf=${tf}`),
        ]);
        if (!alive) return;
        setSchools(s.data?.schools ?? []);
        setIndicators(i.data?.indicators ?? []);
        setConfluence(c.data ?? null);
        setNews(f.data?.news ?? []);
      } catch {}
    }
    pull();
    const id = setInterval(pull, 15000);
    return () => { alive = false; clearInterval(id); };
  }, [symbol, tf]);

  return (
    <div className="grid gap-4">
      <Section title={t('fundamental')}>
        <Table headers={['ts','source','title','sentiment','impact']} rows={news.map(n=>[n.ts?.slice(0,16), n.source, (n.title||'').slice(0,80), n.sentiment, n.impact])} />
      </Section>
      <Section title={t('basics')}>
        <p className="text-xs text-muted">Basic tools (20+) — wired from `basics_pack` worker once enabled.</p>
      </Section>
      <Section title={t('schools')}>
        <Table headers={[t2('school'), t2('result'), t2('share'), t2('weight')]} rows={schools.map(r => [r.code, badge(r.result), r.confidence.toFixed(0), r.weight.toFixed(2)])} />
      </Section>
      <Section title={t('indicators')}>
        <Table headers={[t2('school'), t2('result'), t2('share'), t2('weight')]} rows={indicators.map(r => [r.code, badge(r.result), r.confidence.toFixed(0), r.weight.toFixed(2)])} />
      </Section>
      <Section title={t('flow')}>
        <p className="text-xs text-muted">Order Flow + Bookmap aggregation will populate here once the L2 stream is connected.</p>
      </Section>
      <Section title={t('decision')}>
        {confluence ? (
          <div className="grid grid-cols-3 gap-3 text-xs">
            <KV k="Score (Confluence)" v={`${confluence.total_pct ?? 0}%`} bold />
            <KV k="Decision" v={confluence.decision?.toUpperCase() ?? 'WAIT'} bold />
            <KV k="Direction" v={confluence.payload?.direction ?? '-'} />
            <KV k="Fundamental" v={`${confluence.fundamental_pct ?? 0}/20`} />
            <KV k="Schools" v={`${confluence.schools_pct ?? 0}/30`} />
            <KV k="Indicators" v={`${confluence.indicators_pct ?? 0}/10`} />
          </div>
        ) : <p className="text-xs text-muted">No confluence yet for {symbol} / {tf}.</p>}
      </Section>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-lg border border-[rgba(201,162,39,0.15)] bg-bg-secondary p-4">
      <h3 className="mb-3 text-sm font-semibold text-gold">{title}</h3>
      {children}
    </section>
  );
}

function Table({ headers, rows }: { headers: string[]; rows: any[][] }) {
  return (
    <div className="overflow-x-auto scrollbar-thin">
      <table className="min-w-full text-xs">
        <thead><tr>{headers.map(h => <th key={h} className="px-2 py-1 text-start text-muted font-normal">{h}</th>)}</tr></thead>
        <tbody>
          {rows.length === 0 ? <tr><td className="px-2 py-3 text-muted" colSpan={headers.length}>—</td></tr> :
            rows.map((r, i) => <tr key={i} className="border-t border-[rgba(201,162,39,0.05)] hover:bg-[rgba(201,162,39,0.03)]">{r.map((c, j) => <td key={j} className="px-2 py-1 align-middle">{c}</td>)}</tr>)
          }
        </tbody>
      </table>
    </div>
  );
}

function badge(r: 'buy'|'sell'|'neutral') {
  return <span className={`inline-block rounded px-2 py-0.5 text-[10px] font-semibold ${r==='buy'?'cell-buy':r==='sell'?'cell-sell':'cell-neutral'}`}>{r.toUpperCase()}</span>;
}

function KV({ k, v, bold }: { k: string; v: any; bold?: boolean }) {
  return <div className={`flex flex-col rounded-md border border-[rgba(201,162,39,0.1)] p-2 ${bold ? 'bg-[rgba(201,162,39,0.05)]' : ''}`}><span className="text-[10px] text-muted">{k}</span><span className={`tabular ${bold ? 'text-gold font-semibold' : ''}`}>{String(v)}</span></div>;
}
