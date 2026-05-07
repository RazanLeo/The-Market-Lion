import type { Metadata } from 'next';
import { Tajawal, Inter, Playfair_Display, JetBrains_Mono } from 'next/font/google';
import { NextIntlClientProvider } from 'next-intl';
import { getMessages } from 'next-intl/server';
import '../styles/globals.css';

const tajawal = Tajawal({ subsets: ['arabic'], weight: ['400','500','700','800'], variable: '--font-tajawal', display: 'swap' });
const inter = Inter({ subsets: ['latin'], variable: '--font-inter', display: 'swap' });
const playfair = Playfair_Display({ subsets: ['latin'], variable: '--font-playfair', display: 'swap' });
const jb = JetBrains_Mono({ subsets: ['latin'], variable: '--font-jb', display: 'swap' });

export const metadata: Metadata = {
    title: 'The Market Lion',
    description: 'Razan AI Trading Bot & Indicator',
    icons: { icon: '/brand/logo.jpg' },
};

export default async function RootLayout({ children }: { children: React.ReactNode }) {
    const locale = 'en';
    const dir = 'ltr';
    const messages = await getMessages();
    return (
          <html lang={locale} dir={dir} className={`${tajawal.variable} ${inter.variable} ${playfair.variable} ${jb.variable}`}>
                  <body className="bg-bg-primary text-[var(--text-primary)] antialiased">
                          <NextIntlClientProvider messages={messages} locale={locale}>
                            {children}
                          </NextIntlClientProvider>
                  </body>body>
          </html>html>
        );
}</body>
