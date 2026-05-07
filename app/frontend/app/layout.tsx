import type { Metadata } from 'next';
import { Tajawal, Inter, Playfair_Display, JetBrains_Mono } from 'next/font/google';
import { NextIntlClientProvider } from 'next-intl';
import { getLocale, getMessages } from 'next-intl/server';
import { localeIsRtl, type Locale } from '@/lib/i18n/config';
import '../styles/globals.css';

const tajawal = Tajawal({ subsets: ['arabic'], weight: ['400','500','700','800'], variable: '--font-tajawal', display: 'swap' });
const inter = Inter({ subsets: ['latin'], variable: '--font-inter', display: 'swap' });
const playfair = Playfair_Display({ subsets: ['latin'], variable: '--font-playfair', display: 'swap' });
const jb = JetBrains_Mono({ subsets: ['latin'], variable: '--font-jb', display: 'swap' });

export const metadata: Metadata = {
  title: 'The Market Lion — أسد السوق',
  description: 'Razan AI Trading Bot & Indicator',
  icons: { icon: '/brand/logo.jpg' },
};

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const locale = (await getLocale()) as Locale;
  const messages = await getMessages();
  const dir = localeIsRtl(locale) ? 'rtl' : 'ltr';
  return (
    <html lang={locale} dir={dir} className={`${tajawal.variable} ${inter.variable} ${playfair.variable} ${jb.variable}`}>
      <body className="bg-bg-primary text-[var(--text-primary)] antialiased">
        <NextIntlClientProvider locale={locale} messages={messages}>
          {children}
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
