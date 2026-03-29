"""Skills 扫描器 - 扫描 skills/ 目录，生成 SKILLS_SNAPSHOT"""

import re
from pathlib import Path
from config import SKILLS_DIR


def _parse_skill_frontmatter(skill_path: Path) -> dict | None:
    """解析 SKILL.md 的 YAML Frontmatter 元数据"""
    try:
        content = skill_path.read_text(encoding="utf-8")
    except Exception:
        return None

    dir_name = skill_path.parent.name

    fm_match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not fm_match:
        lines = content.strip().split("\n")
        description = ""
        for line in lines:
            stripped = line.strip().lstrip("#").strip()
            if stripped:
                description = stripped
                break
        return {
            "name": dir_name,
            "description": description or f"技能: {dir_name}",
            "location": f"./backend/skills/{dir_name}/SKILL.md",
        }

    fm_text = fm_match.group(1)
    meta = {}
    for line in fm_text.split("\n"):
        if ":" in line:
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip().strip('"').strip("'")

    display_name = meta.get("name", dir_name)
    description = meta.get("description", f"技能: {display_name}")

    return {
        "name": display_name,
        "description": description,
        "location": f"./backend/skills/{dir_name}/SKILL.md",
    }


def scan_skills() -> list[dict]:
    """扫描 skills 目录下所有的 SKILL.md"""
    skills = []
    if not SKILLS_DIR.exists():
        return skills

    for skill_dir in sorted(SKILLS_DIR.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_file = skill_dir / "SKILL.md"
        if skill_file.exists():
            meta = _parse_skill_frontmatter(skill_file)
            if meta:
                skills.append(meta)

    return skills


def generate_skills_snapshot() -> str:
    """生成 SKILLS_SNAPSHOT 内容（XML 格式，嵌入 System Prompt）"""
    skills = scan_skills()
    if not skills:
        return "<available_skills>\n<!-- 暂无已注册的技能 -->\n</available_skills>"

    lines = ["<available_skills>"]
    for s in skills:
        lines.append("<skill>")
        lines.append(f"<name>{s['name']}</name>")
        lines.append(f"<description>{s['description']}</description>")
        lines.append(f"<location>{s['location']}</location>")
        lines.append("</skill>")
    lines.append("</available_skills>")

    return "\n".join(lines)
