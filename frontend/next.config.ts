import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // スタンドアロンモード（Dockerデプロイ用）
  output: "standalone",

  // 環境変数
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  },

  // 画像最適化設定
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "storage.googleapis.com",
      },
    ],
  },

  // ESLint設定
  eslint: {
    ignoreDuringBuilds: false,
  },

  // TypeScript設定
  typescript: {
    ignoreBuildErrors: false,
  },
};

export default nextConfig;
