import type { Metadata, Viewport } from 'next'
import './globals.css'
import { Providers } from '@/components/ui/Providers'
import { Toaster } from 'react-hot-toast'

export const metadata: Metadata = {
  title: 'أسد السوق — The Market Lion | Razan AI Trading Bot & Indicator',
  description: 'منصة التداول الذكية الأقوى في العالم — بوت ومؤشر التداول الآلي بالذكاء الاصطناعي',
  keywords: ['trading bot', 'forex', 'gold', 'XAUUSD', 'smart money', 'AI trading', 'أسد السوق'],
  icons: {
    icon: '/favicon.ico',
    apple: '/apple-touch-icon.png',
  },
  openGraph: {
    title: 'أسد السوق — The Market Lion',
    description: 'أقوى بوت ومؤشر تداول في العالم',
    type: 'website',
  },
}

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  themeColor: '#C9A227',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ar" dir="rtl" suppressHydrationWarning>
      <body className="bg-dark-300 text-gray-100 antialiased">
        <Providers>
          {children}
          <Toaster
            position="top-center"
            toastOptions={{
              style: {
                background: '#111',
                color: '#f5f5f5',
                border: '1px solid #C9A227',
                borderRadius: '10px',
              },
              success: {
                iconTheme: { primary: '#0E7A2C', secondary: '#fff' },
              },
              error: {
                iconTheme: { primary: '#B0140C', secondary: '#fff' },
              },
            }}
          />
        </Providers>
      </body>
    </html>
  )
}
