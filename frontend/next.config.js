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
};

module.exports = nextConfig;


