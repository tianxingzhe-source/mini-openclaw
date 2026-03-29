"use client";

import { useState } from "react";
import { X, Loader2, Library } from "lucide-react";
import { createKnowledgeBase } from "@/lib/api";

interface CreateKnowledgeModalProps {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}

export default function CreateKnowledgeModal({
  open,
  onClose,
  onCreated,
}: CreateKnowledgeModalProps) {
  const [name, setName] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  if (!open) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    const trimmed = name.trim();
    if (!trimmed) {
      setError("请输入知识库名称");
      return;
    }

    setSaving(true);
    try {
      const res = await createKnowledgeBase(trimmed);
      if (res.success) {
        setName("");
        onCreated();
        onClose();
      } else {
        setError(res.error || "创建失败");
      }
    } catch {
      setError("请求失败，请检查后端服务");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/20 backdrop-blur-sm" onClick={onClose} />

      <div className="relative bg-white rounded-2xl shadow-xl w-[440px] max-h-[85vh] overflow-hidden">
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
          <div className="flex items-center gap-2">
            <Library className="w-4 h-4 text-klein-900" />
            <span className="text-sm font-semibold text-gray-800">新建知识库</span>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg hover:bg-gray-100 text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1.5">
              名称 <span className="text-red-400">*</span>
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="例如：产品文档、内部规范"
              className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg outline-none focus:border-klein-900 focus:ring-1 focus:ring-klein-900/20 transition-all"
            />
            <p className="text-[10px] text-gray-400 mt-1.5 leading-relaxed">
              名称不可重复；勿含 \\ / : * ? &quot; &lt; &gt; | 等字符；最长 64 字。创建后可在下方上传 .md / .txt / .pdf。
            </p>
          </div>

          {error && (
            <p className="text-xs text-red-500 bg-red-50 rounded-lg px-3 py-2">{error}</p>
          )}

          <div className="flex gap-2 pt-1">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 text-xs text-gray-500 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
            >
              取消
            </button>
            <button
              type="submit"
              disabled={saving}
              className="flex-1 px-4 py-2 text-xs text-white bg-klein-900 rounded-lg hover:bg-klein-800 disabled:opacity-50 transition-colors flex items-center justify-center gap-1.5"
            >
              {saving ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Library className="w-3.5 h-3.5" />
              )}
              {saving ? "创建中..." : "创建"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
