"""Agent 核心 - 基于 LangChain create_agent 构建"""

import json
from pathlib import Path
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from config import (
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    MODEL_NAME,
    SESSIONS_DIR,
)
from tools import get_all_tools
from graph.prompt import build_system_prompt


def _get_model() -> ChatOpenAI:
    return ChatOpenAI(
        model=MODEL_NAME,
        api_key=OPENAI_API_KEY,
        base_url=OPENAI_BASE_URL,
        streaming=True,
    )


def get_agent():
    """创建并返回 Agent (CompiledStateGraph)"""
    model = _get_model()
    tools = get_all_tools()
    system_prompt = build_system_prompt()

    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt=system_prompt,
    )
    return agent


def load_session(session_id: str) -> list[dict]:
    """从 JSON 文件加载会话历史"""
    session_file = SESSIONS_DIR / f"{session_id}.json"
    if session_file.exists():
        try:
            data = json.loads(session_file.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except (json.JSONDecodeError, Exception):
            return []
    return []


def save_session(session_id: str, messages: list[dict]):
    """保存会话历史到 JSON 文件"""
    session_file = SESSIONS_DIR / f"{session_id}.json"
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

    serializable = []
    for msg in messages:
        if isinstance(msg, dict):
            serializable.append(msg)
        elif hasattr(msg, "type") and hasattr(msg, "content"):
            entry = {"role": msg.type, "content": msg.content}
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                entry["tool_calls"] = [
                    {
                        "name": tc.get("name", tc.get("function", {}).get("name", "")),
                        "args": tc.get("args", tc.get("function", {}).get("arguments", {})),
                    }
                    for tc in msg.tool_calls
                ]
            if hasattr(msg, "name") and msg.name:
                entry["name"] = msg.name
            if hasattr(msg, "tool_call_id") and msg.tool_call_id:
                entry["tool_call_id"] = msg.tool_call_id
            serializable.append(entry)

    session_file.write_text(
        json.dumps(serializable, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def list_sessions() -> list[dict]:
    """列出所有历史会话"""
    sessions = []
    if not SESSIONS_DIR.exists():
        return sessions

    for f in sorted(SESSIONS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            msg_count = len(data) if isinstance(data, list) else 0
            first_user_msg = ""
            if isinstance(data, list):
                for m in data:
                    if m.get("role") == "user":
                        first_user_msg = m.get("content", "")[:80]
                        break
            sessions.append({
                "id": f.stem,
                "name": first_user_msg or f.stem,
                "message_count": msg_count,
                "updated_at": f.stat().st_mtime,
            })
        except Exception:
            continue

    return sessions
