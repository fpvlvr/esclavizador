import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'export',  // Enable static export for Firebase Hosting
  images: {
    unoptimized: true,  // Firebase Hosting doesn't support next/image optimization
  },
};

export default nextConfig;
