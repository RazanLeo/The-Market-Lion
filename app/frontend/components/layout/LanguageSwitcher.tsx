'use client';

import { useRouter, usePathname } from 'next/navigation';
import { useLocale } from 'next-intl';
import { Globe } from 'lucide-react';
import { localeLabels, locales, type Locale } from '@/lib/i18n/config';
import { useState } from 'react';

export function LanguageSwitcher() {
  const router = useRouter();
  const pathname = usePathname();
  const cur = useLocale() as Locale;
  const [open, setOpen] = useState(false);

  const set = (loc: Locale) => {
    document.cookie = `NEXT_LOCALE=${loc}; path=/; max-age=${60*60*24*365}`;
    setOpen(false);
    router.refresh();
  };

  return (
    <div className="relative">
      <button onClick={() => setOpen(o => !o)} className="flex items-center gap-1 rounded-md p-2 text-gold hover:bg-[rgba(201,162,39,0.08)]" aria-label="Language">
        <Globe size={18} />
        <span className="text-xs font-medium tabular">{localeLabels[cur]?.flag}</span>
      </button>
      {open && (
        <div className="absolute end-0 mt-2 w-56 rounded-md border border-[rgba(201,162,39,0.25)] bg-bg-secondary shadow-glow">
          <ul className="max-h-80 overflow-auto py-1 scrollbar-thin">
            {locales.map(loc => (
              <li key={loc}>
                <button onClick={() => set(loc)} className={`flex w-full items-center justify-between gap-2 px-3 py-1.5 text-sm hover:bg-[rgba(201,162,39,0.08)] ${cur === loc ? 'text-gold' : 'text-muted'}`}>
                  <span>{localeLabels[loc].flag} {localeLabels[loc].native}</span>
                  <span className="text-[10px] uppercase opacity-60">{loc}</span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
