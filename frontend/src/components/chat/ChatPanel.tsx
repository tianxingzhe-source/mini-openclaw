"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { Loader2 } from "lucide-react";
import MessageBubble from "./MessageBubble";
import ChatInput from "./ChatInput";
import { sendMessage, fetchSessionMessages } from "@/lib/api";
import type { Message, ToolCall } from "@/lib/types";

interface ChatPanelProps {
  sessionId: string;
  onMessageSent?: () => void;
}

export default function ChatPanel({ sessionId, onMessageSent }: ChatPanelProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  useEffect(() => {
    let cancelled = false;

    async function loadHistory() {
      setMessages([]);
      setIsLoadingHistory(true);
      try {
        const data = await fetchSessionMessages(sessionId);
        if (cancelled) return;
        const loaded: Message[] = [];
        for (const msg of data.messages || []) {
          if (msg.role === "user" || msg.role === "assistant") {
            loaded.push({
              role: msg.role as "user" | "assistant",
              content: msg.content || "",
              tool_calls: msg.tool_calls as ToolCall[] | undefined,
            });
          }
        }
        setMessages(loaded);
      } catch {
        /* backend not ready or new session */
      } finally {
        if (!cancelled) setIsLoadingHistory(false);
      }
    }

    loadHistory();
    return () => { cancelled = true; };
  }, [sessionId]);

  const handleSend = async (content: string) => {
    const userMsg: Message = {
      role: "user",
      content,
      timestamp: Date.now(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    let assistantContent = "";
    const toolCallsAccum: ToolCall[] = [];

    try {
      await sendMessage(content, sessionId, (event, data) => {
        const d = data as Record<string, unknown>;

        if (event === "tool_call") {
          toolCallsAccum.push({
            name: d.name as string,
            args: d.args as Record<string, unknown>,
          });
        } else if (event === "tool_result") {
          const lastTc = toolCallsAccum[toolCallsAccum.length - 1];
          if (lastTc) {
            lastTc.result = d.result as string;
          }
        } else if (event === "message") {
          assistantContent += d.content as string;
          setMessages((prev) => {
            const copy = [...prev];
            const lastMsg = copy[copy.length - 1];
            if (lastMsg && lastMsg.role === "assistant") {
              return [
                ...copy.slice(0, -1),
                {
                  ...lastMsg,
                  content: assistantContent,
                  tool_calls: [...toolCallsAccum],
                },
              ];
            }
            return [
              ...copy,
              {
                role: "assistant",
                content: assistantContent,
                tool_calls: [...toolCallsAccum],
                timestamp: Date.now(),
              },
            ];
          });
        } else if (event === "error") {
          assistantContent = `出错了: ${d.error || "未知错误"}`;
          setMessages((prev) => [
            ...prev,
            { role: "assistant", content: assistantContent, timestamp: Date.now() },
          ]);
        }
      });

      if (!assistantContent && toolCallsAccum.length > 0) {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: "(已完成工具调用)",
            tool_calls: toolCallsAccum,
            timestamp: Date.now(),
          },
        ]);
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `连接后端失败，请确认服务已启动 (http://localhost:8002)\n\n${err}`,
          timestamp: Date.now(),
        },
      ]);
    } finally {
      setIsLoading(false);
      onMessageSent?.();
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full min-w-0">
      {/* Messages */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto px-6 py-4 space-y-5"
      >
        {isLoadingHistory && (
          <div className="flex items-center justify-center h-full">
            <Loader2 className="w-5 h-5 animate-spin text-gray-300" />
            <span className="ml-2 text-xs text-gray-400">加载历史对话...</span>
          </div>
        )}

        {!isLoadingHistory && messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-gray-300">
            <div className="w-16 h-16 rounded-2xl bg-klein-900/5 flex items-center justify-center mb-4">
              <span className="text-2xl">🤖</span>
            </div>
            <p className="text-sm text-gray-400">开始与 Mini-OpenClaw 对话</p>
            <p className="text-xs text-gray-300 mt-1">
              会话 ID: {sessionId}
            </p>
          </div>
        )}

        {messages.map((msg, i) => (
          <MessageBubble key={i} message={msg} />
        ))}

        {isLoading && messages[messages.length - 1]?.role === "user" && (
          <div className="flex gap-3">
            <div className="w-7 h-7 rounded-full bg-klein-900 flex items-center justify-center flex-shrink-0">
              <span className="text-white text-xs">AI</span>
            </div>
            <div className="typing-indicator flex gap-1 items-center px-4 py-3 bg-white rounded-2xl rounded-tl-md border border-gray-100 shadow-sm">
              <span /><span /><span />
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <ChatInput onSend={handleSend} disabled={isLoading} />
    </div>
  );
}
