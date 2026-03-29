"use client";

import { useState, useCallback, useRef } from "react";
import Navbar from "@/components/navbar/Navbar";
import Sidebar from "@/components/sidebar/Sidebar";
import ChatPanel from "@/components/chat/ChatPanel";
import MonacoWrapper from "@/components/editor/MonacoWrapper";
import { PanelRightOpen, PanelRightClose } from "lucide-react";
import type { SidebarTab } from "@/lib/types";

export default function Home() {
  const [sessionId, setSessionId] = useState("default");
  const [inspectorFile, setInspectorFile] = useState<string | null>(null);
  const [showInspector, setShowInspector] = useState(false);
  const [sidebarTab, setSidebarTab] = useState<SidebarTab>("chat");
  const [sidebarRefreshKey, setSidebarRefreshKey] = useState(0);

  const handleFileSelect = useCallback((path: string) => {
    setInspectorFile(path);
    setShowInspector(true);
  }, []);

  const handleCloseInspector = useCallback(() => {
    setShowInspector(false);
    setInspectorFile(null);
  }, []);

  const handleMessageSent = useCallback(() => {
    setSidebarRefreshKey((k) => k + 1);
  }, []);

  return (
    <div className="h-screen flex flex-col overflow-hidden">
      {/* Top Navbar */}
      <Navbar />

      {/* Main Content (below navbar) */}
      <div className="flex-1 flex pt-12 overflow-hidden">
        {/* Left Sidebar */}
        <Sidebar
          activeSessionId={sessionId}
          onSessionSelect={setSessionId}
          onFileSelect={handleFileSelect}
          activeTab={sidebarTab}
          onTabChange={setSidebarTab}
          refreshKey={sidebarRefreshKey}
        />

        {/* Center Stage */}
        <div className="flex-1 flex flex-col min-w-0 relative">
          {/* Inspector Toggle */}
          <button
            onClick={() => setShowInspector(!showInspector)}
            className="absolute top-3 right-3 z-10 p-1.5 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-all"
            title={showInspector ? "关闭编辑器" : "打开编辑器"}
          >
            {showInspector ? (
              <PanelRightClose className="w-4 h-4" />
            ) : (
              <PanelRightOpen className="w-4 h-4" />
            )}
          </button>

          <ChatPanel sessionId={sessionId} onMessageSent={handleMessageSent} />
        </div>

        {/* Right Inspector */}
        {showInspector && (
          <div className="w-[420px] border-l border-black/5 flex-shrink-0">
            <MonacoWrapper
              filePath={inspectorFile}
              onClose={handleCloseInspector}
            />
          </div>
        )}
      </div>
    </div>
  );
}
