/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  reactStrictMode: true,
  experimental: {
    optimizePackageImports: ['lucide-react'],
  },
  env: {
    NEXT_PUBLIC_TABLE5_API: process.env.NEXT_PUBLIC_TABLE5_API || 'http://localhost:8000',
    NEXT_PUBLIC_TABLE5_WS: process.env.NEXT_PUBLIC_TABLE5_WS || 'ws://localhost:8000',
  },
};

module.exports = nextConfig;
