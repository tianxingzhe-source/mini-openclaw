"use client";

import { useState } from "react";
import { ChevronRight, Wrench, CheckCircle2 } from "lucide-react";
import type { ToolCall } from "@/lib/types";

interface ThoughtChainProps {
  toolCalls: ToolCall[];
}

export default function ThoughtChain({ toolCalls }: ThoughtChainProps) {
  const [expanded, setExpanded] = useState(false);

  if (toolCalls.length === 0) return null;

  return (
    <div className="mb-2">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-1.5 text-[11px] text-gray-400 hover:text-gray-600 transition-colors"
      >
        <ChevronRight
          className={`w-3 h-3 transition-transform ${expanded ? "rotate-90" : ""}`}
        />
        <Wrench className="w-3 h-3" />
        <span>
          已调用 {toolCalls.length} 个工具
        </span>
      </button>

      {expanded && (
        <div className="mt-2 ml-4 space-y-2">
          {toolCalls.map((tc, i) => (
            <div
              key={i}
              className="rounded-lg border border-gray-100 bg-gray-50/50 p-2.5"
            >
              <div className="flex items-center gap-1.5 text-[11px] font-medium text-gray-600">
                <CheckCircle2 className="w-3 h-3 text-green-500" />
                {tc.name}
              </div>
              <div className="mt-1.5 text-[10px] text-gray-400 font-mono bg-white rounded px-2 py-1 overflow-x-auto">
                {JSON.stringify(tc.args, null, 2)}
              </div>
              {tc.result && (
                <div className="mt-1.5 text-[10px] text-gray-500 font-mono bg-white rounded px-2 py-1 max-h-32 overflow-y-auto whitespace-pre-wrap">
                  {tc.result.length > 500
                    ? tc.result.slice(0, 500) + "..."
                    : tc.result}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
