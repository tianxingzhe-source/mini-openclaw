import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Mini-OpenClaw",
  description: "轻量级本地 AI Agent 系统",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body className="bg-surface antialiased">{children}</body>
    </html>
  );
}
