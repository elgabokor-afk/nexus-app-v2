import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // output: "standalone", // DISABLED due to Railway Environment Issues

  images: {
    unoptimized: true,
  },
  async rewrites() {
    return [
      {
        source: '/api/py/:path*',
        destination: process.env.NEXT_PUBLIC_API_URL ? `${process.env.NEXT_PUBLIC_API_URL}/:path*` : 'http://nexus-api.railway.internal:8080/:path*',
      },
    ];
  },
};

export default nextConfig;
