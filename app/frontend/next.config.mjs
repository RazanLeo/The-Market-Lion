import createNextIntlPlugin from 'next-intl/plugin';
const withNextIntl = createNextIntlPlugin('./lib/i18n/request.ts');

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  images: { remotePatterns: [{ protocol: 'https', hostname: '**' }] },
  async rewrites() {
    const api = process.env.PUBLIC_API_URL || 'http://backend:8000';
    return [
      { source: '/api/v1/:path*', destination: `${api}/api/v1/:path*` },
      { source: '/ws/:path*', destination: `${api}/ws/:path*` },
    ];
  },
};

export default withNextIntl(nextConfig);
