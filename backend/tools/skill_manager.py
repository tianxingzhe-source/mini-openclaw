"""技能管理工具 - 支持 Agent 热加载、创建、删除 Skills"""

import re
import shutil
from pathlib import Path

import httpx
import html2text
from langchain_core.tools import tool
from config import SKILLS_DIR

_SAFE_NAME_RE = re.compile(r"^[a-zA-Z0-9_\-]+$")


def _sanitize_name(name: str) -> str | None:
    """校验技能名称，防止路径穿越"""
    name = name.strip().lower().replace(" ", "_").replace("-", "_")
    if not name or not _SAFE_NAME_RE.match(name):
        return None
    return name


def _extract_frontmatter_name(content: str) -> str | None:
    """从 SKILL.md 内容中提取 name 字段"""
    fm = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not fm:
        return None
    for line in fm.group(1).split("\n"):
        if line.strip().startswith("name:"):
            return line.split(":", 1)[1].strip().strip('"').strip("'")
    return None


def create_install_skill_tool():
    @tool("install_skill")
    def install_skill(name: str, content: str = "", url: str = "") -> str:
        """安装一个新的 Agent Skill。可以通过 URL 下载或直接提供 SKILL.md 内容。
        安装后，该技能会在下一轮对话中自动出现在你的技能列表里。

        【重要】SKILL.md 的全部内容（包括 description）必须使用简体中文！
        如果从 URL 下载到英文内容，你必须先将其翻译为中文，再作为 content 参数传入。
        禁止直接将英文内容写入！

        使用方式：
        1. 从 URL 安装（先下载翻译再安装）：
           a. 用 fetch_url 获取内容
           b. 将内容翻译为中文
           c. 调用 install_skill(name="...", content="翻译后的中文内容")
        2. 直接创建：install_skill(name="skill_name", content="---\\nname: ...\\n---\\n# ...")

        Args:
            name: 技能名称（英文、数字、下划线，用作文件夹名）
            content: SKILL.md 的完整 Markdown 内容（必须是中文！与 url 二选一）
            url: 远程 SKILL.md 文件的 URL 地址（内容将自动下载，但你仍需确保翻译为中文）
        """
        safe_name = _sanitize_name(name)
        if not safe_name:
            return f"⚠️ 技能名称不合法: '{name}'。只允许英文字母、数字和下划线。"

        if not content and not url:
            return "⚠️ 必须提供 content（SKILL.md 内容）或 url（远程地址）之一。"

        if url and not content:
            try:
                with httpx.Client(timeout=15, follow_redirects=True) as client:
                    resp = client.get(url, headers={
                        "User-Agent": "MiniOpenClaw-SkillInstaller/1.0"
                    })
                    resp.raise_for_status()

                ctype = resp.headers.get("content-type", "")
                raw = resp.text

                if "text/html" in ctype:
                    converter = html2text.HTML2Text()
                    converter.ignore_links = False
                    converter.body_width = 0
                    raw = converter.handle(raw)

                content = raw
            except httpx.HTTPStatusError as e:
                return f"⚠️ 下载失败 HTTP {e.response.status_code}: {url}"
            except Exception as e:
                return f"⚠️ 下载失败: {str(e)}"

        if not content.strip():
            return "⚠️ 获取到的内容为空，安装取消。"

        embedded_name = _extract_frontmatter_name(content)
        if embedded_name:
            safe_embedded = _sanitize_name(embedded_name)
            if safe_embedded:
                safe_name = safe_embedded

        skill_dir = SKILLS_DIR / safe_name
        skill_file = skill_dir / "SKILL.md"

        is_update = skill_file.exists()

        try:
            skill_dir.mkdir(parents=True, exist_ok=True)
            skill_file.write_text(content, encoding="utf-8")
        except Exception as e:
            return f"⚠️ 写入失败: {str(e)}"

        action = "更新" if is_update else "安装"
        return (
            f"✅ 技能 `{safe_name}` {action}成功！\n"
            f"📁 路径: skills/{safe_name}/SKILL.md\n"
            f"该技能将在下一轮对话中自动生效。"
        )

    return install_skill


def create_remove_skill_tool():
    @tool("remove_skill")
    def remove_skill(name: str) -> str:
        """删除一个已安装的 Agent Skill。

        Args:
            name: 要删除的技能名称
        """
        safe_name = _sanitize_name(name)
        if not safe_name:
            return f"⚠️ 技能名称不合法: '{name}'"

        skill_dir = SKILLS_DIR / safe_name
        if not skill_dir.exists():
            return f"⚠️ 技能 `{safe_name}` 不存在。"

        try:
            shutil.rmtree(skill_dir)
            return f"✅ 技能 `{safe_name}` 已删除，下一轮对话中将不再出现。"
        except Exception as e:
            return f"⚠️ 删除失败: {str(e)}"

    return remove_skill


def create_list_available_skills_tool():
    @tool("list_skills")
    def list_skills() -> str:
        """列出当前所有已安装的 Agent Skills，包括名称、描述和路径。"""
        from graph.skills_scanner import scan_skills

        skills = scan_skills()
        if not skills:
            return "当前没有已安装的技能。可以使用 install_skill 工具来安装新技能。"

        lines = [f"当前已安装 {len(skills)} 个技能：\n"]
        for s in skills:
            lines.append(f"- **{s['name']}**: {s['description']}")
            lines.append(f"  📁 {s['location']}")
        return "\n".join(lines)

    return list_skills
