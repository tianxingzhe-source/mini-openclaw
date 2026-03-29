"use client";

import { useState, useEffect, useCallback } from "react";
import dynamic from "next/dynamic";
import { Save, X, FileText, Loader2 } from "lucide-react";
import { readFile, saveFile } from "@/lib/api";

const Editor = dynamic(() => import("@monaco-editor/react"), { ssr: false });

interface MonacoWrapperProps {
  filePath: string | null;
  onClose: () => void;
}

export default function MonacoWrapper({ filePath, onClose }: MonacoWrapperProps) {
  const [content, setContent] = useState("");
  const [originalContent, setOriginalContent] = useState("");
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState<"idle" | "saved" | "error">("idle");

  const loadFile = useCallback(async (path: string) => {
    setLoading(true);
    try {
      const data = await readFile(path);
      if (data.content !== undefined && data.content !== null) {
        setContent(data.content);
        setOriginalContent(data.content);
      }
    } catch {
      setContent("// 无法加载文件");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (filePath) {
      loadFile(filePath);
      setSaveStatus("idle");
    }
  }, [filePath, loadFile]);

  const handleSave = async () => {
    if (!filePath) return;
    setSaving(true);
    try {
      const res = await saveFile(filePath, content);
      if (res.success) {
        setOriginalContent(content);
        setSaveStatus("saved");
        setTimeout(() => setSaveStatus("idle"), 2000);
      } else {
        setSaveStatus("error");
      }
    } catch {
      setSaveStatus("error");
    } finally {
      setSaving(false);
    }
  };

  const hasChanges = content !== originalContent;

  const getLanguage = (path: string | null): string => {
    if (!path) return "markdown";
    if (path.endsWith(".md")) return "markdown";
    if (path.endsWith(".json")) return "json";
    if (path.endsWith(".yaml") || path.endsWith(".yml")) return "yaml";
    if (path.endsWith(".py")) return "python";
    return "markdown";
  };

  if (!filePath) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-gray-300 bg-white/40">
        <FileText className="w-10 h-10 mb-3 opacity-40" />
        <p className="text-xs text-gray-400">从侧边栏选择文件查看</p>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-gray-100 bg-gray-50/50">
        <div className="flex items-center gap-2 min-w-0">
          <FileText className="w-3.5 h-3.5 text-gray-400 flex-shrink-0" />
          <span className="text-xs text-gray-600 truncate font-mono">
            {filePath}
          </span>
          {hasChanges && (
            <span className="w-2 h-2 rounded-full bg-orange-400 flex-shrink-0" />
          )}
        </div>
        <div className="flex items-center gap-1">
          {saveStatus === "saved" && (
            <span className="text-[10px] text-green-500 mr-1">已保存</span>
          )}
          {saveStatus === "error" && (
            <span className="text-[10px] text-red-500 mr-1">保存失败</span>
          )}
          <button
            onClick={handleSave}
            disabled={saving || !hasChanges}
            className={`p-1.5 rounded-md transition-colors ${
              hasChanges
                ? "text-klein-900 hover:bg-klein-900/10"
                : "text-gray-300 cursor-not-allowed"
            }`}
            title="保存 (Ctrl+S)"
          >
            {saving ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Save className="w-3.5 h-3.5" />
            )}
          </button>
          <button
            onClick={onClose}
            className="p-1.5 rounded-md text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Editor */}
      <div className="flex-1 min-h-0">
        {loading ? (
          <div className="h-full flex items-center justify-center">
            <Loader2 className="w-5 h-5 animate-spin text-gray-300" />
          </div>
        ) : (
          <Editor
            height="100%"
            language={getLanguage(filePath)}
            theme="vs"
            value={content}
            onChange={(val) => setContent(val || "")}
            options={{
              fontSize: 13,
              fontFamily: "'SF Mono', 'Fira Code', 'Consolas', monospace",
              lineHeight: 22,
              minimap: { enabled: false },
              scrollBeyondLastLine: false,
              wordWrap: "on",
              padding: { top: 12, bottom: 12 },
              renderLineHighlight: "none",
              overviewRulerLanes: 0,
              hideCursorInOverviewRuler: true,
              scrollbar: {
                verticalScrollbarSize: 6,
                horizontalScrollbarSize: 6,
              },
            }}
          />
        )}
      </div>
    </div>
  );
}
