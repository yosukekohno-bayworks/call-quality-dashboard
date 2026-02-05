import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // 背景色
        "bg-primary": "#F8FAFC",
        "bg-card": "#FFFFFF",
        "bg-sidebar": "#1E293B",

        // テキスト色
        "text-primary": "#0F172A",
        "text-secondary": "#64748B",

        // アクセントカラー
        "accent-primary": "#3B82F6",

        // ステータス色
        "status-success": "#10B981",
        "status-warning": "#F59E0B",
        "status-error": "#EF4444",
      },
      fontFamily: {
        sans: ["Inter", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      borderRadius: {
        sm: "4px",
        md: "8px",
        lg: "12px",
      },
    },
  },
  plugins: [],
};

export default config;
