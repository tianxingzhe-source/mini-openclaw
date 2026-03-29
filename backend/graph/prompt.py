"""System Prompt 动态拼接引擎

按照以下顺序拼接 System Prompt:
1. SKILLS_SNAPSHOT.md (能力列表)
2. SOUL.md (核心设定)
3. IDENTITY.md (自我认知)
4. USER.md (用户画像)
5. AGENTS.md (行为准则 & 记忆操作指南)
6. MEMORY.md (长期记忆)

超过 MAX_PROMPT_CHARS 时自动截断。
"""

from pathlib import Path
from config import WORKSPACE_DIR, MEMORY_DIR, SKILLS_DIR, MAX_PROMPT_CHARS
from graph.skills_scanner import generate_skills_snapshot


def _read_file_safe(path: Path, label: str) -> str:
    if not path.exists():
        return ""
    try:
        content = path.read_text(encoding="utf-8").strip()
        if len(content) > MAX_PROMPT_CHARS:
            content = content[:MAX_PROMPT_CHARS] + "\n\n...[truncated]"
        return content
    except Exception:
        return ""


def build_system_prompt() -> str:
    """动态组装完整的 System Prompt"""
    snapshot = generate_skills_snapshot()

    parts = [
        ("SKILLS_SNAPSHOT", snapshot),
        ("SOUL", _read_file_safe(WORKSPACE_DIR / "SOUL.md", "SOUL")),
        ("IDENTITY", _read_file_safe(WORKSPACE_DIR / "IDENTITY.md", "IDENTITY")),
        ("USER", _read_file_safe(WORKSPACE_DIR / "USER.md", "USER")),
        ("AGENTS", _read_file_safe(WORKSPACE_DIR / "AGENTS.md", "AGENTS")),
        ("MEMORY", _read_file_safe(MEMORY_DIR / "MEMORY.md", "MEMORY")),
    ]

    sections = []
    for label, content in parts:
        if content:
            sections.append(content)

    full_prompt = "\n\n---\n\n".join(sections)

    if len(full_prompt) > MAX_PROMPT_CHARS * 6:
        full_prompt = full_prompt[: MAX_PROMPT_CHARS * 6] + "\n\n...[truncated]"

    return full_prompt
