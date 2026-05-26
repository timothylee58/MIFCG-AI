import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  experimental: {
    serverActions: {
      allowedOrigins: ["localhost:3000", "*.pages.dev", "*.koyeb.app"],
    },
  },
};

export default nextConfig;
