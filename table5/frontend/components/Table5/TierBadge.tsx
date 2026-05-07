// ═══════════════════════════════════════════════════════════════════════════
// 🦁 شارة Tier (S/A/B/C) — ألوان متدرجة من الذهبي للنحاسي
// ═══════════════════════════════════════════════════════════════════════════
'use client';

const TIER_COLORS: Record<string, string> = {
  S: 'bg-[#C9A227] text-black',
  A: 'bg-amber-600 text-black',
  B: 'bg-zinc-500 text-white',
  C: 'bg-stone-700 text-stone-300',
};

export function TierBadge({ tier }: { tier: 'S' | 'A' | 'B' | 'C' | string }) {
  return (
    <span
      className={`inline-flex h-5 w-5 items-center justify-center rounded-full text-[10px] font-bold ${
        TIER_COLORS[tier] ?? 'bg-zinc-700 text-zinc-400'
      }`}
    >
      {tier}
    </span>
  );
}
