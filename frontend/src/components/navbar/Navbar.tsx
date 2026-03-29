"use client";

import { Cpu } from "lucide-react";

export default function Navbar() {
  return (
    <header className="fixed top-0 left-0 right-0 z-50 h-12 glass-strong flex items-center justify-between px-5 border-b border-black/5">
      <div className="flex items-center gap-2.5">
        <div className="w-7 h-7 rounded-lg bg-klein-900 flex items-center justify-center">
          <Cpu className="w-4 h-4 text-white" />
        </div>
        <span className="text-sm font-semibold tracking-tight text-gray-800">
          mini OpenClaw
        </span>
        <span className="text-[10px] font-medium text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded">
          v1.0
        </span>
      </div>

      <a
        href="https://github.com/tianxingzhe-source"
        target="_blank"
        rel="noopener noreferrer"
        className="text-xs text-gray-500 hover:text-klein-900 transition-colors"
      >
        天行者
      </a>
    </header>
  );
}
