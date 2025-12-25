/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  
  // Enable standalone output for Docker
  output: 'standalone',
  
  // Code splitting optimization
  experimental: {
    optimizePackageImports: ['@/components', '@/lib'],
  },

  // Image optimization
  images: {
    domains: [],
  },

  // Headers для правильной работы кэширования
  async headers() {
    return [
      {
        // Статические файлы с хешами можно кэшировать долго
        source: '/_next/static/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable',
          },
        ],
      },
    ];
  },
};

module.exports = nextConfig;


