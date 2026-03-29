"""知识库目录与文件管理（多库，每库为 knowledge/<name>/ 子目录）"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from config import KNOWLEDGE_DIR

ALLOWED_EXTENSIONS = {".md", ".txt", ".pdf"}
_INVALID_NAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
MANIFEST_NAME = ".kb_manifest.json"


def validate_kb_name(name: str) -> tuple[str | None, str | None]:
    """返回 (规范化名称, 错误信息)。"""
    s = (name or "").strip()
    if not s:
        return None, "名称不能为空"
    if len(s) > 64:
        return None, "名称最长 64 个字符"
    if s in (".", ".."):
        return None, "无效名称"
    if len(Path(s).parts) != 1:
        return None, "名称不能包含路径分隔符"
    if _INVALID_NAME_CHARS.search(s):
        return None, "名称不能包含 \\ / : * ? \" < > | 等字符"
    return s, None


def kb_dir(name: str) -> Path:
    return KNOWLEDGE_DIR / name


def kb_name_exists(name: str) -> bool:
    """名称唯一（大小写不敏感，与 Windows 行为一致）。"""
    return resolve_kb_folder_name(name) is not None


def resolve_kb_folder_name(name: str) -> str | None:
    """返回磁盘上实际目录名（大小写不敏感匹配）。"""
    if not KNOWLEDGE_DIR.exists():
        return None
    key = name.strip().lower()
    for child in KNOWLEDGE_DIR.iterdir():
        if child.is_dir() and child.name.lower() == key:
            return child.name
    return None


def ensure_knowledge_root() -> None:
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)


def _manifest_path(kb_real: str) -> Path:
    return kb_dir(kb_real) / MANIFEST_NAME


def load_manifest(kb_real: str) -> dict:
    p = _manifest_path(kb_real)
    if not p.exists():
        return {"files": {}}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return {"files": {}}
        data.setdefault("files", {})
        if not isinstance(data["files"], dict):
            data["files"] = {}
        return data
    except (json.JSONDecodeError, OSError):
        return {"files": {}}


def save_manifest(kb_real: str, data: dict) -> None:
    p = _manifest_path(kb_real)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def sync_manifest_for_kb(kb_real: str) -> None:
    """与磁盘上的允许扩展名文件对齐 manifest（新文件默认未解析，已删文件移除条目）。"""
    root = kb_dir(kb_real)
    if not root.is_dir():
        return
    on_disk = {
        f.name
        for f in root.iterdir()
        if f.is_file() and f.suffix.lower() in ALLOWED_EXTENSIONS
    }
    m = load_manifest(kb_real)
    files = m["files"]
    # 移除已不存在的文件记录
    for key in list(files.keys()):
        if key not in on_disk:
            del files[key]
    # 新文件默认未解析
    for name in on_disk:
        if name not in files:
            files[name] = {"parsed": False, "parse_error": None, "parsed_at": None}
    save_manifest(kb_real, m)


def register_uploaded_file(kb_real: str, filename: str) -> None:
    """上传后登记为未解析。"""
    m = load_manifest(kb_real)
    m.setdefault("files", {})
    m["files"][filename] = {"parsed": False, "parse_error": None, "parsed_at": None}
    save_manifest(kb_real, m)


def set_file_parse_result(
    kb_real: str,
    filename: str,
    *,
    parsed: bool,
    error: str | None,
    parsed_at: str | None = None,
) -> None:
    m = load_manifest(kb_real)
    m.setdefault("files", {})
    entry = m["files"].get(filename, {})
    entry["parsed"] = parsed
    entry["parse_error"] = error
    if parsed_at is not None:
        entry["parsed_at"] = parsed_at
    elif not parsed:
        entry["parsed_at"] = None
    m["files"][filename] = entry
    save_manifest(kb_real, m)


def remove_file_from_manifest(kb_real: str, filename: str) -> None:
    m = load_manifest(kb_real)
    m.setdefault("files", {})
    m["files"].pop(filename, None)
    save_manifest(kb_real, m)


def list_parsed_absolute_paths(kb_real: str) -> list[Path]:
    """供 RAG 建索引：仅已解析文件的绝对路径。"""
    sync_manifest_for_kb(kb_real)
    m = load_manifest(kb_real)
    root = kb_dir(kb_real)
    out: list[Path] = []
    for fname, meta in m.get("files", {}).items():
        if not isinstance(meta, dict):
            continue
        if not meta.get("parsed"):
            continue
        p = root / fname
        if p.is_file() and p.suffix.lower() in ALLOWED_EXTENSIONS:
            out.append(p)
    return out


def list_knowledge_bases() -> list[dict]:
    ensure_knowledge_root()
    out: list[dict] = []
    for p in sorted(KNOWLEDGE_DIR.iterdir(), key=lambda x: x.name.lower()):
        if not p.is_dir() or p.name.startswith("."):
            continue
        sync_manifest_for_kb(p.name)
        m = load_manifest(p.name)
        meta_files = m.get("files", {})
        file_entries = []
        for f in sorted(p.iterdir(), key=lambda x: x.name.lower()):
            if not f.is_file() or f.suffix.lower() not in ALLOWED_EXTENSIONS:
                continue
            info = meta_files.get(f.name, {})
            if not isinstance(info, dict):
                info = {}
            file_entries.append(
                {
                    "name": f.name,
                    "parsed": bool(info.get("parsed")),
                    "parse_error": info.get("parse_error"),
                }
            )
        out.append({"name": p.name, "files": file_entries})
    return out


def create_knowledge_base(name: str) -> tuple[bool, str | None]:
    normalized, err = validate_kb_name(name)
    if err:
        return False, err
    ensure_knowledge_root()
    if kb_name_exists(normalized):
        return False, "已存在同名知识库"
    try:
        kb_dir(normalized).mkdir(parents=False)
        save_manifest(normalized, {"files": {}})
    except OSError as e:
        return False, str(e)
    return True, None


def safe_upload_basename(filename: str) -> tuple[str | None, str | None]:
    base = Path(filename or "").name
    if not base or base in (".", ".."):
        return None, "无效文件名"
    if _INVALID_NAME_CHARS.search(base):
        return None, "文件名包含非法字符"
    ext = Path(base).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return None, "仅支持 .md、.txt、.pdf 文件"
    return base, None


def write_kb_file(
    kb_name: str, filename: str, data: bytes
) -> tuple[bool, str | None, str | None]:
    """成功时第三项为磁盘上的知识库目录名（用于失效索引缓存）。"""
    real = resolve_kb_folder_name(kb_name)
    if not real:
        return False, "知识库不存在", None
    safe_name, err = safe_upload_basename(filename)
    if err:
        return False, err, None
    dest = kb_dir(real) / safe_name
    try:
        dest.write_bytes(data)
    except OSError as e:
        return False, str(e), None
    register_uploaded_file(real, safe_name)
    return True, None, real


def delete_kb_file(
    kb_name: str, filename: str
) -> tuple[bool, str | None, str | None]:
    real = resolve_kb_folder_name(kb_name)
    if not real:
        return False, "知识库不存在", None
    safe_name, err = safe_upload_basename(filename)
    if err:
        return False, err, None
    path = kb_dir(real) / safe_name
    if not path.is_file():
        return False, "文件不存在", None
    try:
        path.unlink()
    except OSError as e:
        return False, str(e), None
    remove_file_from_manifest(real, safe_name)
    return True, None, real


def delete_knowledge_base(kb_name: str) -> tuple[str | None, str | None]:
    """成功时返回 (实际目录名, None)，失败返回 (None, 错误信息)。"""
    real_name = resolve_kb_folder_name(kb_name)
    if not real_name:
        return None, "知识库不存在"
    real = KNOWLEDGE_DIR / real_name
    try:
        shutil.rmtree(real)
    except OSError as e:
        return None, str(e)
    return real_name, None
