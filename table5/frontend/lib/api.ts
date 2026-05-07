// ═══════════════════════════════════════════════════════════════════════════
// 🦁 طبقة استدعاء API الجدول الخامس
// ═══════════════════════════════════════════════════════════════════════════

const API_BASE = process.env.NEXT_PUBLIC_TABLE5_API || 'http://localhost:8000';
const WS_BASE = process.env.NEXT_PUBLIC_TABLE5_WS || 'ws://localhost:8000';

export interface IndicatorMeta {
  id: number;
  name: string;
  category: string;
  category_en: string;
  tier: 'S' | 'A' | 'B' | 'C';
  weight: number;
  weight_pct: number;
  min_bars: number;
}

export interface IndicatorRow {
  indicator_id: number;
  indicator_name: string;
  category: string;
  tier: 'S' | 'A' | 'B' | 'C';
  weight: number;
  signals: Record<string, 'شراء' | 'بيع' | 'محايد'>;
  weighted_score: number;
  confidence: number;
  direction: string;
  raw_values: Record<string, number | null>;
}

export interface Decision {
  symbol: string;
  timestamp: string;
  net_score: number;
  confidence: number;
  decision: 'شراء' | 'بيع' | 'محايد';
  signal_level: string;
  filters: {
    choppiness_applied: boolean;
    htf_veto_applied: boolean;
    convergence_boost: boolean;
    tier_s_consensus: number;
  };
  indicators: IndicatorRow[];
}

export interface Meta {
  module_weight_pct: number;
  indicators_count: number;
  timeframes: string[];
  timeframe_weights: Record<string, number>;
  tier_values: Record<string, number>;
  total_tier_sum: number;
  signal_thresholds: Record<string, number>;
  decision_threshold: number;
  tier_distribution: Record<string, number>;
  category_distribution: Record<string, number>;
}

export async function fetchMeta(): Promise<Meta> {
  const r = await fetch(`${API_BASE}/api/v1/table-5/meta`, { cache: 'no-store' });
  if (!r.ok) throw new Error(`/meta failed: ${r.status}`);
  return r.json();
}

export async function fetchIndicators(): Promise<IndicatorMeta[]> {
  const r = await fetch(`${API_BASE}/api/v1/table-5/indicators`, { cache: 'no-store' });
  if (!r.ok) throw new Error(`/indicators failed: ${r.status}`);
  return r.json();
}

export async function fetchDecision(symbol: string): Promise<Decision> {
  const url = new URL(`${API_BASE}/api/v1/table-5/decision`);
  url.searchParams.set('symbol', symbol);
  url.searchParams.set('include_indicators', 'true');
  const r = await fetch(url.toString(), { cache: 'no-store' });
  if (!r.ok) throw new Error(`/decision failed: ${r.status}`);
  return r.json();
}

export function openTable5Stream(
  symbol: string,
  onMessage: (d: Decision) => void,
  onError?: (e: Event) => void,
): WebSocket {
  const ws = new WebSocket(`${WS_BASE}/api/v1/table-5/ws/${encodeURIComponent(symbol)}`);
  ws.onmessage = (ev) => {
    try {
      const data = JSON.parse(ev.data);
      if (data.type === 'table5_update') onMessage(data);
    } catch {}
  };
  if (onError) ws.onerror = onError;
  return ws;
}
