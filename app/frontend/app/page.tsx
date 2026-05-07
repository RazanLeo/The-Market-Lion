import Link from 'next/link';
import { useTranslations } from 'next-intl';
import { Header } from '@/components/layout/Header';
import { Footer } from '@/components/layout/Footer';
import { TickersStrip } from '@/components/layout/TickersStrip';
import { Logo } from '@/components/brand/Logo';

export default function HomePage() {
  const t = useTranslations();
  return (
    <>
      <Header />
      <TickersStrip />

      <main className="mx-auto max-w-[1500px] px-6 py-16">
        <section className="mx-auto flex max-w-3xl flex-col items-center text-center">
          <Logo size={120} withText={false} />
          <h1 className="mt-6 font-display text-5xl text-gold leading-tight">{t('brand.name')}</h1>
          <p className="mt-2 text-lg text-muted">{t('brand.subtitle')}</p>
          <p className="mt-4 max-w-xl text-sm text-muted/90">{t('brand.tagline')}</p>
          <div className="mt-8 flex gap-3">
            <Link href="/auth/register" className="rounded-md bg-gold px-6 py-3 text-bg-primary font-semibold hover:shadow-glow">{t('nav.register')}</Link>
            <Link href="/auth/login" className="rounded-md border border-gold px-6 py-3 text-gold hover:shadow-glow-soft">{t('nav.login')}</Link>
          </div>
        </section>
      </main>

      <Footer />
    </>
  );
}
