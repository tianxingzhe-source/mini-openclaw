"""Mini-OpenClaw 后端入口 - FastAPI 服务 (Port 8002)"""

import asyncio
import json
import uuid
from pathlib import Path

import uvicorn
from fastapi import FastAPI, File, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from config import PORT, BASE_DIR, SESSIONS_DIR, MEMORY_DIR, SKILLS_DIR, WORKSPACE_DIR
from knowledge_store import (
    create_knowledge_base,
    delete_kb_file,
    delete_knowledge_base,
    list_knowledge_bases,
    validate_kb_name,
    write_kb_file,
)
from knowledge_parse import parse_kb_file
from tools.rag_search import invalidate_kb_index_cache
from graph.agent import get_agent, load_session, save_session, list_sessions

app = FastAPI(
    title="Mini-OpenClaw",
    description="轻量级本地 AI Agent 系统",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── 请求/响应模型 ──────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"
    stream: bool = True


class FileSaveRequest(BaseModel):
    path: str
    content: str


class KnowledgeBaseCreateRequest(BaseModel):
    name: str


class KnowledgeParseRequest(BaseModel):
    filename: str


# ── 对话接口 ────────────────────────────────────────────────

def _messages_to_langchain(messages: list[dict]) -> list[dict]:
    """将存储的消息格式转换为 LangChain 消息格式"""
    lc_messages = []
    for msg in messages:
        role = msg.get("role", "")
        content = msg.get("content", "")
        if role == "user":
            lc_messages.append({"role": "user", "content": content})
        elif role in ("assistant", "ai"):
            lc_messages.append({"role": "assistant", "content": content})
    return lc_messages


@app.post("/api/chat")
async def chat(req: ChatRequest):
    """发送用户消息，获取 Agent 回复（支持 SSE 流式输出）"""

    history = load_session(req.session_id)
    history.append({"role": "user", "content": req.message})

    lc_messages = _messages_to_langchain(history)
    agent = get_agent()

    if req.stream:
        return EventSourceResponse(
            _stream_agent(agent, lc_messages, history, req.session_id),
            media_type="text/event-stream",
        )
    else:
        result = await asyncio.to_thread(
            agent.invoke, {"messages": lc_messages}
        )
        final_messages = result.get("messages", [])
        assistant_content = ""
        if final_messages:
            last_msg = final_messages[-1]
            assistant_content = getattr(last_msg, "content", str(last_msg))

        history.append({"role": "assistant", "content": assistant_content})
        save_session(req.session_id, history)
        return {"response": assistant_content, "session_id": req.session_id}


async def _stream_agent(agent, lc_messages, history, session_id):
    """流式处理 Agent 响应，输出 SSE 事件"""
    full_response = ""
    tool_calls_log = []

    try:
        # 使用 astream_events 逐事件推送，避免 list(...) 聚合导致“假流式”。
        async for event in agent.astream_events(
            {"messages": lc_messages},
            version="v2",
        ):
            event_name = event.get("event", "")
            data = event.get("data", {}) or {}

            if event_name == "on_chat_model_stream":
                chunk = data.get("chunk")
                content = ""

                if chunk is not None:
                    chunk_content = getattr(chunk, "content", "")
                    if isinstance(chunk_content, str):
                        content = chunk_content
                    elif isinstance(chunk_content, list):
                        parts = []
                        for item in chunk_content:
                            if isinstance(item, str):
                                parts.append(item)
                            elif isinstance(item, dict) and item.get("type") == "text":
                                parts.append(item.get("text", ""))
                        content = "".join(parts)

                if content:
                    full_response += content
                    yield {
                        "event": "message",
                        "data": json.dumps({"content": content}, ensure_ascii=False),
                    }

            elif event_name == "on_tool_start":
                tool_name = event.get("name", "")
                tool_args = data.get("input", {})
                if not isinstance(tool_args, dict):
                    tool_args = {"input": str(tool_args)}

                tool_info = {"name": tool_name, "args": tool_args}
                tool_calls_log.append(tool_info)
                yield {
                    "event": "tool_call",
                    "data": json.dumps(tool_info, ensure_ascii=False),
                }

            elif event_name == "on_tool_end":
                tool_name = event.get("name", "")
                output = data.get("output", "")
                output_text = output if isinstance(output, str) else str(output)
                yield {
                    "event": "tool_result",
                    "data": json.dumps(
                        {"name": tool_name, "result": output_text[:2000]},
                        ensure_ascii=False,
                    ),
                }

    except Exception as e:
        yield {
            "event": "error",
            "data": json.dumps({"error": str(e)}, ensure_ascii=False),
        }

    if full_response:
        history.append({"role": "assistant", "content": full_response})
    if tool_calls_log:
        history.append({"role": "tool_log", "tool_calls": tool_calls_log})

    save_session(session_id, history)

    yield {
        "event": "done",
        "data": json.dumps({"session_id": session_id}, ensure_ascii=False),
    }


# ── 文件管理接口 ────────────────────────────────────────────

@app.get("/api/files")
async def read_file(path: str = Query(..., description="文件相对路径")):
    """读取指定文件的内容"""
    file_path = (BASE_DIR / path).resolve()
    base_resolved = BASE_DIR.resolve()

    if not str(file_path).startswith(str(base_resolved)):
        return {"error": "不允许访问项目目录以外的文件", "content": None}

    if not file_path.exists():
        return {"error": f"文件不存在: {path}", "content": None}

    try:
        content = file_path.read_text(encoding="utf-8")
        return {"path": path, "content": content}
    except Exception as e:
        return {"error": str(e), "content": None}


@app.post("/api/files")
async def save_file(req: FileSaveRequest):
    """保存对 Memory 或 Skill 文件的修改"""
    file_path = (BASE_DIR / req.path).resolve()
    base_resolved = BASE_DIR.resolve()

    if not str(file_path).startswith(str(base_resolved)):
        return {"error": "不允许写入项目目录以外的文件"}

    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(req.content, encoding="utf-8")
        return {"success": True, "path": req.path}
    except Exception as e:
        return {"error": str(e)}


# ── 会话管理接口 ────────────────────────────────────────────

@app.get("/api/sessions")
async def get_sessions():
    """获取所有历史会话列表"""
    return {"sessions": list_sessions()}


@app.get("/api/sessions/{session_id}")
async def get_session_messages(session_id: str):
    """获取指定会话的完整消息历史"""
    messages = load_session(session_id)
    return {"session_id": session_id, "messages": messages}


@app.post("/api/sessions")
async def create_session():
    """创建新会话"""
    session_id = str(uuid.uuid4())[:8]
    save_session(session_id, [])
    return {"session_id": session_id}


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    """删除指定会话"""
    session_file = SESSIONS_DIR / f"{session_id}.json"
    if session_file.exists():
        session_file.unlink()
        return {"success": True}
    return {"error": "会话不存在"}


# ── 知识库接口 ───────────────────────────────────────────────

@app.get("/api/knowledge-bases")
async def api_list_knowledge_bases():
    """列出所有知识库及其文件"""
    return {"knowledge_bases": list_knowledge_bases()}


@app.post("/api/knowledge-bases")
async def api_create_knowledge_base(req: KnowledgeBaseCreateRequest):
    ok, err = create_knowledge_base(req.name)
    if not ok:
        return {"success": False, "error": err}
    normalized, _ = validate_kb_name(req.name)
    return {"success": True, "name": normalized}


@app.post("/api/knowledge-bases/{kb_name}/upload")
async def api_upload_knowledge_file(
    kb_name: str,
    file: UploadFile = File(...),
    auto_parse: bool = Query(False, description="上传成功后是否立即解析"),
):
    data = await file.read()
    if len(data) > 50 * 1024 * 1024:
        return {"success": False, "error": "单文件大小不能超过 50MB"}
    ok, err, canonical = write_kb_file(kb_name, file.filename or "", data)
    if not ok:
        return {"success": False, "error": err}
    if canonical:
        invalidate_kb_index_cache(canonical)
    saved_name = Path(file.filename or "").name
    if auto_parse:
        parse_ok, parse_err = await asyncio.to_thread(parse_kb_file, kb_name, saved_name)
        return {
            "success": True,
            "filename": saved_name,
            "parsed": parse_ok,
            "parse_error": parse_err,
        }
    return {"success": True, "filename": saved_name, "parsed": False}


@app.post("/api/knowledge-bases/{kb_name}/parse")
async def api_parse_knowledge_file(kb_name: str, req: KnowledgeParseRequest):
    parse_ok, parse_err = await asyncio.to_thread(
        parse_kb_file, kb_name, req.filename
    )
    if not parse_ok:
        return {"success": False, "error": parse_err or "解析失败"}
    result: dict = {"success": True, "filename": req.filename}
    if parse_err:
        result["warning"] = parse_err
    return result


@app.delete("/api/knowledge-bases/{kb_name}/files/{filename:path}")
async def api_delete_knowledge_file(kb_name: str, filename: str):
    ok, err, canonical = delete_kb_file(kb_name, filename)
    if not ok:
        return {"success": False, "error": err}
    if canonical:
        invalidate_kb_index_cache(canonical)
    return {"success": True}


@app.delete("/api/knowledge-bases/{kb_name}")
async def api_delete_knowledge_base(kb_name: str):
    real_name, err = delete_knowledge_base(kb_name)
    if err:
        return {"success": False, "error": err}
    if real_name:
        invalidate_kb_index_cache(real_name)
    return {"success": True}


# ── Skills 接口 ─────────────────────────────────────────────

class SkillCreateRequest(BaseModel):
    name: str
    description: str = ""
    content: str = ""


@app.get("/api/skills")
async def get_skills():
    """获取所有已注册的 Skills 列表"""
    from graph.skills_scanner import scan_skills
    return {"skills": scan_skills()}


@app.post("/api/skills")
async def create_skill(req: SkillCreateRequest):
    """通过前端界面创建新技能"""
    import re
    name = req.name.strip().lower().replace(" ", "_").replace("-", "_")
    if not name or not re.match(r"^[a-zA-Z0-9_]+$", name):
        return {"error": "技能名称只允许英文字母、数字和下划线"}

    skill_dir = SKILLS_DIR / name
    skill_file = skill_dir / "SKILL.md"

    content = req.content.strip()
    if not content:
        content = f"""---
name: {name}
description: {req.description or f'技能: {name}'}
---

# {name}

## 功能说明

{req.description or '请填写技能功能描述。'}

## 使用步骤

1. 使用相关工具执行任务...

## 示例

具体调用示例。

## 注意事项

使用限制和注意点。
"""

    is_update = skill_file.exists()
    try:
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_file.write_text(content, encoding="utf-8")
        action = "更新" if is_update else "创建"
        return {"success": True, "name": name, "message": f"技能 {name} {action}成功"}
    except Exception as e:
        return {"error": str(e)}


@app.delete("/api/skills/{skill_name}")
async def delete_skill_api(skill_name: str):
    """删除指定技能"""
    import re
    import shutil
    name = skill_name.strip().lower()
    if not name or not re.match(r"^[a-zA-Z0-9_]+$", name):
        return {"error": "技能名称不合法"}

    skill_dir = SKILLS_DIR / name
    if not skill_dir.exists():
        return {"error": f"技能 {name} 不存在"}

    try:
        shutil.rmtree(skill_dir)
        return {"success": True, "name": name}
    except Exception as e:
        return {"error": str(e)}


# ── 文件树接口（前端 Inspector 用）────────────────────────────

@app.get("/api/file-tree")
async def get_file_tree():
    """获取可编辑的文件树结构"""
    tree = []

    for category, directory in [
        ("workspace", WORKSPACE_DIR),
        ("memory", MEMORY_DIR),
        ("skills", SKILLS_DIR),
    ]:
        if not directory.exists():
            continue
        for f in sorted(directory.rglob("*")):
            if f.is_file() and f.suffix in (".md", ".json", ".txt", ".yaml"):
                rel = f.relative_to(BASE_DIR)
                tree.append({
                    "category": category,
                    "path": str(rel).replace("\\", "/"),
                    "name": f.name,
                })

    return {"files": tree}


# ── 入口 ────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=PORT, reload=True)
