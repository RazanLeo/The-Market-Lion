import { getRequestConfig } from 'next-intl/server';
import { notFound } from 'next/navigation';
import { locales, defaultLocale, type Locale } from './config';

export default getRequestConfig(async ({ locale }) => {
  if (!locale || !locales.includes(locale as Locale)) {
    locale = defaultLocale;
  }
  let messages;
  try {
    messages = (await import(`../../messages/${locale}.json`)).default;
  } catch {
    messages = (await import(`../../messages/${defaultLocale}.json`)).default;
  }
  return { locale, messages };
});
