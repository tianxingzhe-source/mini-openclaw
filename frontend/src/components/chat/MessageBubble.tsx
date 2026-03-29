"use client";

import { User, Bot } from "lucide-react";
import ThoughtChain from "./ThoughtChain";
import type { Message } from "@/lib/types";

interface MessageBubbleProps {
  message: Message;
}

function renderMarkdown(text: string) {
  let html = text
    .replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code class="language-$1">$2</code></pre>')
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    .replace(/^### (.+)$/gm, "<h3>$1</h3>")
    .replace(/^## (.+)$/gm, "<h2>$1</h2>")
    .replace(/^# (.+)$/gm, "<h1>$1</h1>")
    .replace(/^> (.+)$/gm, "<blockquote>$1</blockquote>")
    .replace(/^- (.+)$/gm, "<li>$1</li>")
    .replace(/\n/g, "<br/>");

  html = html.replace(/(<li>.*<\/li>)/gs, "<ul>$1</ul>");
  html = html.replace(/<\/ul><br\/><ul>/g, "");

  return html;
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  if (message.role === "tool_log") return null;

  return (
    <div className={`flex gap-3 ${isUser ? "flex-row-reverse" : ""}`}>
      {/* Avatar */}
      <div
        className={`w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 ${
          isUser
            ? "bg-gray-200 text-gray-600"
            : "bg-klein-900 text-white"
        }`}
      >
        {isUser ? <User className="w-3.5 h-3.5" /> : <Bot className="w-3.5 h-3.5" />}
      </div>

      {/* Content */}
      <div className={`max-w-[75%] ${isUser ? "text-right" : ""}`}>
        {!isUser && message.tool_calls && message.tool_calls.length > 0 && (
          <ThoughtChain toolCalls={message.tool_calls} />
        )}

        <div
          className={`inline-block rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
            isUser
              ? "bg-klein-900 text-white rounded-tr-md"
              : "bg-white border border-gray-100 text-gray-700 rounded-tl-md shadow-sm"
          }`}
        >
          {isUser ? (
            <p>{message.content}</p>
          ) : (
            <div
              className="markdown-content"
              dangerouslySetInnerHTML={{ __html: renderMarkdown(message.content) }}
            />
          )}
        </div>
      </div>
    </div>
  );
}
