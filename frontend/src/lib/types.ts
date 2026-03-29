export interface Message {
  role: "user" | "assistant" | "tool_log";
  content: string;
  tool_calls?: ToolCall[];
  timestamp?: number;
}

export interface ToolCall {
  name: string;
  args: Record<string, unknown>;
  result?: string;
}

export interface Session {
  id: string;
  name: string;
  message_count: number;
  updated_at: number;
}

export interface Skill {
  name: string;
  description: string;
  location: string;
}

export interface FileNode {
  category: string;
  path: string;
  name: string;
}

export type SidebarTab = "chat" | "memory" | "skills" | "knowledge";

export interface KnowledgeFileEntry {
  name: string;
  parsed: boolean;
  parse_error?: string | null;
}

export interface KnowledgeBase {
  name: string;
  files: KnowledgeFileEntry[];
}
