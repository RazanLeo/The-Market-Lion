import Image from 'next/image';
import { useTranslations } from 'next-intl';

export function Logo({ size = 36, withText = true }: { size?: number; withText?: boolean }) {
  const t = useTranslations('brand');
  return (
    <div className="flex items-center gap-3">
      <Image src="/brand/logo.jpg" alt={t('name')} width={size} height={size} priority className="rounded-md drop-shadow-[0_0_12px_rgba(201,162,39,0.4)]" />
      {withText && (
        <div className="flex flex-col leading-tight">
          <span className="text-gold font-display text-lg font-bold">{t('name')}</span>
          <span className="text-muted text-[11px] tracking-wide">{t('subtitle')}</span>
        </div>
      )}
    </div>
  );
}
