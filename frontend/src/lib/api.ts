const API_BASE = "http://localhost:8002";

export async function sendMessage(
  message: string,
  sessionId: string,
  onEvent: (event: string, data: unknown) => void
): Promise<void> {
  const response = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, session_id: sessionId, stream: true }),
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }

  const reader = response.body?.getReader();
  if (!reader) throw new Error("No response body");

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    let currentEvent = "message";
    for (const line of lines) {
      if (line.startsWith("event:")) {
        currentEvent = line.slice(6).trim();
      } else if (line.startsWith("data:")) {
        const dataStr = line.slice(5).trim();
        if (dataStr) {
          try {
            const data = JSON.parse(dataStr);
            onEvent(currentEvent, data);
          } catch {
            onEvent(currentEvent, { raw: dataStr });
          }
        }
      }
    }
  }
}

export async function fetchSessions(): Promise<{ sessions: Array<{ id: string; name: string; message_count: number; updated_at: number }> }> {
  const res = await fetch(`${API_BASE}/api/sessions`);
  return res.json();
}

export async function fetchSessionMessages(sessionId: string): Promise<{ session_id: string; messages: Array<{ role: string; content?: string; tool_calls?: Array<{ name: string; args: Record<string, unknown> }> }> }> {
  const res = await fetch(`${API_BASE}/api/sessions/${encodeURIComponent(sessionId)}`);
  return res.json();
}

export async function createSession(): Promise<{ session_id: string }> {
  const res = await fetch(`${API_BASE}/api/sessions`, { method: "POST" });
  return res.json();
}

export async function deleteSession(sessionId: string): Promise<void> {
  await fetch(`${API_BASE}/api/sessions/${sessionId}`, { method: "DELETE" });
}

export async function readFile(path: string): Promise<{ path: string; content: string; error?: string }> {
  const res = await fetch(`${API_BASE}/api/files?path=${encodeURIComponent(path)}`);
  return res.json();
}

export async function saveFile(path: string, content: string): Promise<{ success?: boolean; error?: string }> {
  const res = await fetch(`${API_BASE}/api/files`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ path, content }),
  });
  return res.json();
}

export async function fetchSkills(): Promise<{ skills: Array<{ name: string; description: string; location: string }> }> {
  const res = await fetch(`${API_BASE}/api/skills`);
  return res.json();
}

export async function createSkill(name: string, description: string, content?: string): Promise<{ success?: boolean; name?: string; error?: string }> {
  const res = await fetch(`${API_BASE}/api/skills`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, description, content: content || "" }),
  });
  return res.json();
}

export async function deleteSkill(name: string): Promise<{ success?: boolean; error?: string }> {
  const res = await fetch(`${API_BASE}/api/skills/${encodeURIComponent(name)}`, { method: "DELETE" });
  return res.json();
}

export async function fetchFileTree(): Promise<{ files: Array<{ category: string; path: string; name: string }> }> {
  const res = await fetch(`${API_BASE}/api/file-tree`);
  return res.json();
}

export async function fetchKnowledgeBases(): Promise<{
  knowledge_bases: Array<{
    name: string;
    files: Array<{ name: string; parsed: boolean; parse_error?: string | null }>;
  }>;
}> {
  const res = await fetch(`${API_BASE}/api/knowledge-bases`);
  return res.json();
}

export async function createKnowledgeBase(
  name: string
): Promise<{ success?: boolean; name?: string; error?: string }> {
  const res = await fetch(`${API_BASE}/api/knowledge-bases`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
  return res.json();
}

export async function uploadKnowledgeFile(
  kbName: string,
  file: File,
  autoParse = false
): Promise<{
  success?: boolean;
  filename?: string;
  parsed?: boolean;
  parse_error?: string | null;
  error?: string;
}> {
  const fd = new FormData();
  fd.append("file", file);
  const q = autoParse ? "?auto_parse=true" : "";
  const res = await fetch(
    `${API_BASE}/api/knowledge-bases/${encodeURIComponent(kbName)}/upload${q}`,
    { method: "POST", body: fd }
  );
  return res.json();
}

export async function parseKnowledgeFile(
  kbName: string,
  filename: string
): Promise<{ success?: boolean; filename?: string; error?: string }> {
  const res = await fetch(
    `${API_BASE}/api/knowledge-bases/${encodeURIComponent(kbName)}/parse`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ filename }),
    }
  );
  return res.json();
}

export async function deleteKnowledgeFile(
  kbName: string,
  filename: string
): Promise<{ success?: boolean; error?: string }> {
  const res = await fetch(
    `${API_BASE}/api/knowledge-bases/${encodeURIComponent(kbName)}/files/${encodeURIComponent(filename)}`,
    { method: "DELETE" }
  );
  return res.json();
}

export async function deleteKnowledgeBase(
  kbName: string
): Promise<{ success?: boolean; error?: string }> {
  const res = await fetch(
    `${API_BASE}/api/knowledge-bases/${encodeURIComponent(kbName)}`,
    { method: "DELETE" }
  );
  return res.json();
}
