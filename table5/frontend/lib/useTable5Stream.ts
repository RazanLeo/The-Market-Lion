// ═══════════════════════════════════════════════════════════════════════════
// 🦁 React Hook للتدفق اللحظي لقرار الجدول الخامس
// ═══════════════════════════════════════════════════════════════════════════
'use client';

import { useEffect, useState, useRef } from 'react';
import { Decision, fetchDecision, openTable5Stream } from './api';

export function useTable5Stream(symbol: string) {
  const [decision, setDecision] = useState<Decision | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    let cancelled = false;
    setError(null);

    // 1. أول جلب REST لتعبئة فورية
    fetchDecision(symbol)
      .then((d) => { if (!cancelled) setDecision(d); })
      .catch((e) => { if (!cancelled) setError(String(e)); });

    // 2. ثم WebSocket للتحديث اللحظي
    const ws = openTable5Stream(
      symbol,
      (d) => { if (!cancelled) setDecision(d); },
      (e) => { if (!cancelled) setError('WebSocket error'); },
    );
    wsRef.current = ws;
    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);

    return () => {
      cancelled = true;
      ws.close();
    };
  }, [symbol]);

  return { decision, error, connected };
}
