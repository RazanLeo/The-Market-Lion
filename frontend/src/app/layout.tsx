import type { Metadata } from 'next'
import './globals.css'
import { Toaster } from 'react-hot-toast'

export const metadata: Metadata = {
  title: 'أسد السوق | The Market Lion',
  description: 'أقوى بوت تداول بالذكاء الاصطناعي - The Most Powerful AI Trading Bot',
  keywords: 'trading, gold, forex, AI, bot, تداول, ذهب, فوركس, روبوت',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ar" dir="rtl" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="bg-dark-900 text-white font-cairo antialiased">
        {children}
        <Toaster
          position="top-center"
          toastOptions={{
            style: {
              background: '#1A1A1A',
              color: '#fff',
              border: '1px solid rgba(201, 162, 39, 0.3)',
              fontFamily: 'Cairo, sans-serif',
            },
            success: {
              iconTheme: { primary: '#C9A227', secondary: '#000' },
            },
            error: {
              iconTheme: { primary: '#B0140C', secondary: '#fff' },
            },
          }}
        />
      </body>
    </html>
  )
}
