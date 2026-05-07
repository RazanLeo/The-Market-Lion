import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: '🦁 The Market Lion — Table 5',
  description: 'الجدول الخامس: 71 مؤشر فني × 6 أطر زمنية',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ar" dir="rtl">
      <body>{children}</body>
    </html>
  );
}
