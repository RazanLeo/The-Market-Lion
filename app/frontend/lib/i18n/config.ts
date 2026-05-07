export const locales = [
  'en','ar','pt-BR','pt-PT','es','fr','de','ru','tr','zh-CN','ja','ko'
] as const;
export type Locale = typeof locales[number];
export const defaultLocale: Locale = 'en';
export const rtlLocales: Locale[] = ['ar'];

export function localeIsRtl(loc: Locale): boolean {
  return rtlLocales.includes(loc);
}

export const localeLabels: Record<Locale, { native: string; english: string; flag: string }> = {
  en:    { native: 'English',     english: 'English',                       flag: '🇬🇧' },
  ar:    { native: 'العربية',     english: 'Arabic',                        flag: '🇸🇦' },
  'pt-BR':{ native: 'Português (Brasil)', english: 'Portuguese (Brazil)',  flag: '🇧🇷' },
  'pt-PT':{ native: 'Português',  english: 'Portuguese',                    flag: '🇵🇹' },
  es:    { native: 'Español',     english: 'Spanish',                       flag: '🇪🇸' },
  fr:    { native: 'Français',    english: 'French',                        flag: '🇫🇷' },
  de:    { native: 'Deutsch',     english: 'German',                        flag: '🇩🇪' },
  ru:    { native: 'Русский',     english: 'Russian',                       flag: '🇷🇺' },
  tr:    { native: 'Türkçe',      english: 'Turkish',                       flag: '🇹🇷' },
  'zh-CN':{ native: '简体中文',    english: 'Chinese (Simplified)',         flag: '🇨🇳' },
  ja:    { native: '日本語',       english: 'Japanese',                      flag: '🇯🇵' },
  ko:    { native: '한국어',       english: 'Korean',                        flag: '🇰🇷' },
};
