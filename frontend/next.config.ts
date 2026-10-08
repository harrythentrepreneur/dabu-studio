import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Enable standalone output for Docker deployment
  output: 'standalone',

  // Ensure environment variables are available
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || '',
    NEXT_PUBLIC_BACKEND_URL: process.env.NEXT_PUBLIC_BACKEND_URL || '',
    NEXT_PUBLIC_CLOUD: process.env.NEXT_PUBLIC_CLOUD || 'false',
    NEXT_DISABLE_FONT_DOWNLOADS: '1',
  },

  // Optional: Add any other configurations
  reactStrictMode: true,

  // Temporarily skip build errors for faster Docker testing
  typescript: {
    ignoreBuildErrors: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
};

export default nextConfig;