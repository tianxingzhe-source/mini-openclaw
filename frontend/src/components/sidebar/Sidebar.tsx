"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import {
  MessageSquare,
  Brain,
  Puzzle,
  Plus,
  Trash2,
  FileText,
  Library,
  Upload,
} from "lucide-react";
import {
  fetchSessions,
  createSession,
  deleteSession,
  fetchSkills,
  fetchFileTree,
  deleteSkill,
  fetchKnowledgeBases,
  uploadKnowledgeFile,
  parseKnowledgeFile,
  deleteKnowledgeFile,
  deleteKnowledgeBase,
} from "@/lib/api";
import CreateSkillModal from "@/components/modals/CreateSkillModal";
import CreateKnowledgeModal from "@/components/modals/CreateKnowledgeModal";
import type { Session, Skill, FileNode, SidebarTab, KnowledgeBase } from "@/lib/types";

interface SidebarProps {
  activeSessionId: string;
  onSessionSelect: (id: string) => void;
  onFileSelect: (path: string) => void;
  activeTab: SidebarTab;
  onTabChange: (tab: SidebarTab) => void;
  refreshKey?: number;
}

const tabs: { id: SidebarTab; label: string; icon: React.ElementType }[] = [
  { id: "chat", label: "对话", icon: MessageSquare },
  { id: "memory", label: "记忆", icon: Brain },
  { id: "skills", label: "技能", icon: Puzzle },
  { id: "knowledge", label: "知识库", icon: Library },
];

export default function Sidebar({
  activeSessionId,
  onSessionSelect,
  onFileSelect,
  activeTab,
  onTabChange,
  refreshKey = 0,
}: SidebarProps) {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [skills, setSkills] = useState<Skill[]>([]);
  const [files, setFiles] = useState<FileNode[]>([]);
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [showCreateSkill, setShowCreateSkill] = useState(false);
  const [showCreateKnowledge, setShowCreateKnowledge] = useState(false);
  const [pendingUploadKb, setPendingUploadKb] = useState<string | null>(null);
  const [uploadBusy, setUploadBusy] = useState(false);
  const [autoParseOnUpload, setAutoParseOnUpload] = useState(false);
  const [parsingKey, setParsingKey] = useState<string | null>(null);
  const kbFileInputRef = useRef<HTMLInputElement>(null);

  const loadData = useCallback(async () => {
    try {
      if (activeTab === "chat") {
        const data = await fetchSessions();
        setSessions(data.sessions || []);
      } else if (activeTab === "skills") {
        const data = await fetchSkills();
        setSkills(data.skills || []);
      } else if (activeTab === "memory") {
        const data = await fetchFileTree();
        setFiles((data.files || []).filter((f) => f.category === "workspace" || f.category === "memory"));
      } else if (activeTab === "knowledge") {
        const data = await fetchKnowledgeBases();
        setKnowledgeBases(data.knowledge_bases || []);
      }
    } catch {
      /* backend not ready */
    }
  }, [activeTab]);

  useEffect(() => {
    loadData();
  }, [loadData, refreshKey]);

  const handleNewSession = async () => {
    try {
      const data = await createSession();
      onSessionSelect(data.session_id);
      loadData();
    } catch { /* ignore */ }
  };

  const handleDeleteSession = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await deleteSession(id);
      if (activeSessionId === id) onSessionSelect("default");
      loadData();
    } catch { /* ignore */ }
  };

  return (
    <aside className="w-56 h-full flex flex-col border-r border-black/5 bg-white/60">
      {/* Tab Nav */}
      <div className="flex border-b border-black/5">
        {tabs.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => onTabChange(id)}
            className={`flex-1 flex flex-col items-center gap-0.5 py-2.5 text-[10px] font-medium transition-colors ${
              activeTab === id
                ? "text-klein-900 border-b-2 border-klein-900"
                : "text-gray-400 hover:text-gray-600"
            }`}
          >
            <Icon className="w-4 h-4" />
            {label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-2">
        {activeTab === "chat" && (
          <>
            <button
              onClick={handleNewSession}
              className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-xs text-gray-500 hover:bg-gray-100 transition-colors mb-1"
            >
              <Plus className="w-3.5 h-3.5" />
              新建对话
            </button>
            {sessions.map((s) => (
              <div
                key={s.id}
                onClick={() => onSessionSelect(s.id)}
                className={`group flex items-center justify-between px-3 py-2 rounded-lg cursor-pointer text-xs transition-colors mb-0.5 ${
                  activeSessionId === s.id
                    ? "bg-klein-900/8 text-klein-900 font-medium"
                    : "text-gray-600 hover:bg-gray-50"
                }`}
              >
                <span className="truncate flex-1">{s.name || s.id}</span>
                <button
                  onClick={(e) => handleDeleteSession(s.id, e)}
                  className="opacity-0 group-hover:opacity-100 p-0.5 hover:text-red-500 transition-all"
                >
                  <Trash2 className="w-3 h-3" />
                </button>
              </div>
            ))}
            {sessions.length === 0 && (
              <p className="text-[11px] text-gray-400 text-center mt-4">
                暂无对话记录
              </p>
            )}
          </>
        )}

        {activeTab === "memory" && (
          <>
            {files.map((f) => (
              <div
                key={f.path}
                onClick={() => onFileSelect(f.path)}
                className="flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer text-xs text-gray-600 hover:bg-gray-50 transition-colors mb-0.5"
              >
                <FileText className="w-3.5 h-3.5 text-gray-400 flex-shrink-0" />
                <span className="truncate">{f.name}</span>
              </div>
            ))}
            {files.length === 0 && (
              <p className="text-[11px] text-gray-400 text-center mt-4">
                暂无文件
              </p>
            )}
          </>
        )}

        {activeTab === "skills" && (
          <>
            <button
              onClick={() => setShowCreateSkill(true)}
              className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-xs text-gray-500 hover:bg-gray-100 transition-colors mb-1"
            >
              <Plus className="w-3.5 h-3.5" />
              新建技能
            </button>
            {skills.map((s) => (
              <div
                key={s.name}
                onClick={() => onFileSelect(s.location.replace("./backend/", ""))}
                className="group px-3 py-2.5 rounded-lg cursor-pointer hover:bg-gray-50 transition-colors mb-0.5"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 min-w-0">
                    <Puzzle className="w-3.5 h-3.5 text-klein-900 flex-shrink-0" />
                    <span className="text-xs font-medium text-gray-700 truncate">
                      {s.name}
                    </span>
                  </div>
                  <button
                    onClick={async (e) => {
                      e.stopPropagation();
                      if (!confirm(`确定删除技能「${s.name}」吗？`)) return;
                      try {
                        await deleteSkill(s.name);
                        loadData();
                      } catch { /* ignore */ }
                    }}
                    className="opacity-0 group-hover:opacity-100 p-0.5 hover:text-red-500 transition-all flex-shrink-0"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                </div>
                <p className="text-[10px] text-gray-400 mt-1 ml-5.5 leading-relaxed truncate">
                  {s.description}
                </p>
              </div>
            ))}
            {skills.length === 0 && (
              <p className="text-[11px] text-gray-400 text-center mt-4">
                暂无已注册技能
              </p>
            )}
            <CreateSkillModal
              open={showCreateSkill}
              onClose={() => setShowCreateSkill(false)}
              onCreated={() => loadData()}
            />
          </>
        )}

        {activeTab === "knowledge" && (
          <>
            <label className="flex items-center gap-2 px-2 py-1.5 mb-2 text-[10px] text-gray-600 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={autoParseOnUpload}
                onChange={(e) => setAutoParseOnUpload(e.target.checked)}
                className="rounded border-gray-300 text-klein-900 focus:ring-klein-900/30"
              />
              上传后自动解析
            </label>
            <button
              onClick={() => setShowCreateKnowledge(true)}
              className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-xs text-gray-500 hover:bg-gray-100 transition-colors mb-1"
            >
              <Plus className="w-3.5 h-3.5" />
              新建知识库
            </button>
            <input
              ref={kbFileInputRef}
              type="file"
              accept=".md,.txt,.pdf"
              className="hidden"
              onChange={async (e) => {
                const kb = pendingUploadKb;
                const f = e.target.files?.[0];
                e.target.value = "";
                setPendingUploadKb(null);
                if (!kb || !f) return;
                setUploadBusy(true);
                try {
                  const res = await uploadKnowledgeFile(kb, f, autoParseOnUpload);
                  if (!res.success) {
                    alert(res.error || "上传失败");
                  } else if (autoParseOnUpload && res.parsed === false && res.parse_error) {
                    alert(`上传成功，自动解析失败：${res.parse_error}`);
                  }
                  loadData();
                } catch {
                  alert("上传失败");
                } finally {
                  setUploadBusy(false);
                }
              }}
            />
            {knowledgeBases.map((kb) => (
              <div
                key={kb.name}
                className="mb-2 rounded-lg border border-black/5 bg-white/80 overflow-hidden"
              >
                <div className="flex items-center justify-between gap-1 px-2 py-1.5 bg-gray-50/80">
                  <span className="text-[11px] font-medium text-gray-800 truncate flex-1 min-w-0">
                    {kb.name}
                  </span>
                  <button
                    type="button"
                    title="上传文件"
                    disabled={uploadBusy}
                    onClick={() => {
                      setPendingUploadKb(kb.name);
                      kbFileInputRef.current?.click();
                    }}
                    className="p-1 rounded text-gray-500 hover:bg-gray-200/80 disabled:opacity-40"
                  >
                    <Upload className="w-3.5 h-3.5" />
                  </button>
                  <button
                    type="button"
                    title="删除知识库"
                    onClick={async () => {
                      if (!confirm(`确定删除知识库「${kb.name}」及其全部文件？`)) return;
                      try {
                        await deleteKnowledgeBase(kb.name);
                        loadData();
                      } catch {
                        /* ignore */
                      }
                    }}
                    className="p-1 rounded text-gray-400 hover:text-red-500 hover:bg-gray-200/80"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
                <div className="px-2 py-1 space-y-1">
                  {kb.files.length === 0 ? (
                    <p className="text-[10px] text-gray-400 py-1">暂无文件，点击 ↑ 上传</p>
                  ) : (
                    kb.files.map((file) => {
                      const pk = `${kb.name}/${file.name}`;
                      const busy = parsingKey === pk;
                      return (
                        <div
                          key={file.name}
                          className="group flex flex-col gap-0.5 py-1 border-b border-black/[0.04] last:border-0"
                        >
                          <div className="flex items-start justify-between gap-1">
                            <div className="flex items-center gap-1 min-w-0 flex-1">
                              <FileText className="w-3 h-3 text-gray-400 flex-shrink-0 mt-0.5" />
                              <span className="text-[10px] text-gray-700 truncate" title={file.name}>
                                {file.name}
                              </span>
                            </div>
                            <div className="flex items-center gap-0.5 flex-shrink-0">
                              {!file.parsed && (
                                <button
                                  type="button"
                                  disabled={busy}
                                  onClick={async () => {
                                    setParsingKey(pk);
                                    try {
                                      const res = await parseKnowledgeFile(kb.name, file.name);
                                      if (!res.success) {
                                        alert(res.error || "解析失败");
                                      } else if ((res as Record<string, unknown>).warning) {
                                        alert((res as Record<string, unknown>).warning);
                                      }
                                      loadData();
                                    } catch {
                                      alert("解析请求失败");
                                    } finally {
                                      setParsingKey(null);
                                    }
                                  }}
                                  className="text-[9px] px-1.5 py-0.5 rounded bg-klein-900/10 text-klein-900 hover:bg-klein-900/15 disabled:opacity-50"
                                >
                                  {busy ? "…" : "解析"}
                                </button>
                              )}
                              <button
                                type="button"
                                title="删除文件"
                                onClick={async () => {
                                  if (!confirm(`删除文件「${file.name}」？`)) return;
                                  try {
                                    await deleteKnowledgeFile(kb.name, file.name);
                                    loadData();
                                  } catch {
                                    /* ignore */
                                  }
                                }}
                                className="p-0.5 text-gray-300 hover:text-red-500 opacity-0 group-hover:opacity-100"
                              >
                                <Trash2 className="w-3 h-3" />
                              </button>
                            </div>
                          </div>
                          <div className="flex items-center gap-1 pl-4">
                            <span
                              className={`text-[9px] px-1 rounded ${
                                file.parsed
                                  ? "bg-emerald-50 text-emerald-700"
                                  : "bg-amber-50 text-amber-800"
                              }`}
                            >
                              {file.parsed ? "已解析 · 可检索" : "待解析"}
                            </span>
                          </div>
                          {file.parse_error && (
                            <p className="text-[9px] text-red-500 pl-4 leading-snug break-words">
                              {file.parse_error}
                            </p>
                          )}
                        </div>
                      );
                    })
                  )}
                </div>
              </div>
            ))}
            {knowledgeBases.length === 0 && (
              <p className="text-[11px] text-gray-400 text-center mt-4 px-2">
                暂无知识库。新建后上传 .md / .txt / .pdf，解析后即可被 Agent 检索。
              </p>
            )}
            <CreateKnowledgeModal
              open={showCreateKnowledge}
              onClose={() => setShowCreateKnowledge(false)}
              onCreated={() => loadData()}
            />
          </>
        )}
      </div>
    </aside>
  );
}
