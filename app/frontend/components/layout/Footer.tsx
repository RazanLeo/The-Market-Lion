import Link from 'next/link';
import { useTranslations } from 'next-intl';
import { Logo } from '../brand/Logo';

export function Footer() {
  const t = useTranslations('footer');
  return (
    <footer className="mt-12 border-t border-[rgba(201,162,39,0.15)] bg-[#080808]">
      <div className="mx-auto grid max-w-[1500px] gap-8 px-6 py-12 md:grid-cols-5">
        <div className="md:col-span-2">
          <Logo />
          <p className="mt-3 max-w-md text-sm text-muted leading-relaxed">{t('disclaimer')}</p>
        </div>
        <FooterCol title={t('services')} links={[
          { href: '/dashboard', label: t('services') },
          { href: '/subscribe', label: t('quickstart') },
        ]} />
        <FooterCol title={t('guide')} links={[
          { href: '/docs/user-guide', label: t('guide') },
          { href: '/docs/quickstart', label: t('quickstart') },
          { href: '/docs/faq', label: t('faq') },
          { href: '/support', label: t('support') },
        ]} />
        <FooterCol title="Legal" links={[
          { href: '/legal/terms', label: t('terms') },
          { href: '/legal/privacy', label: t('privacy') },
          { href: '/legal/risk', label: t('risk') },
          { href: '/legal/cookies', label: t('cookies') },
          { href: '/legal/aml', label: t('aml') },
        ]} />
      </div>
      <div className="border-t border-[rgba(201,162,39,0.10)] py-3 text-center text-[11px] text-muted">{t('rights')}</div>
    </footer>
  );
}

function FooterCol({ title, links }: { title: string; links: { href: string; label: string }[] }) {
  return (
    <div>
      <h4 className="mb-2 text-sm font-semibold text-gold">{title}</h4>
      <ul className="space-y-1.5 text-xs">
        {links.map(l => (
          <li key={l.href}><Link href={l.href} className="text-muted hover:text-gold">{l.label}</Link></li>
        ))}
      </ul>
    </div>
  );
}
