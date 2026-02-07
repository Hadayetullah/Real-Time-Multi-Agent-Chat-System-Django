import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  
  // Enable strict mode for better development experience
  reactStrictMode: true,
  
  // Standalone output for production Docker builds
  // This creates a minimal standalone build with only necessary files
  output: process.env.NODE_ENV === 'production' ? 'standalone' : undefined,
  
  // Configure image optimization with remotePatterns (replaces deprecated domains)
  // This allows Next.js to optimize images from specified sources
  images: {
    remotePatterns: [
      {
        protocol: 'http',      // Allow HTTP protocol (for local development)
        hostname: 'localhost', // Allow localhost images
        port: '',              // Any port
        pathname: '/**',       // All paths
      },
      {
        protocol: 'https',     // Allow HTTPS protocol (for production)
        hostname: '**',        // Allow all HTTPS domains (can be restricted)
        port: '',
        pathname: '/**',
      },
    ],
  },
  
  // Environment variables available to the client
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
};

export default nextConfig;