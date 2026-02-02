// import type { NextConfig } from "next";

// const nextConfig: NextConfig = {
//   /* config options here */
// };

// export default nextConfig;



import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  
  // Enable strict mode for better development experience
  reactStrictMode: true,
  
  // Standalone output for production Docker builds
  // This creates a minimal standalone build with only necessary files
  output: process.env.NODE_ENV === 'production' ? 'standalone' : undefined,
  
  // Configure image optimization domains if needed
  images: {
    domains: ['localhost'],
  },
  
  // Environment variables available to the client
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
};

export default nextConfig;