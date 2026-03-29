"""知识库文件解析 → 分块 → 构建向量索引 → 持久化"""

from __future__ import annotations

from datetime import datetime, timezone

from knowledge_store import (
    kb_dir,
    resolve_kb_folder_name,
    safe_upload_basename,
    set_file_parse_result,
)
from tools.rag_search import invalidate_kb_index_cache, build_kb_index


def parse_kb_file(kb_name: str, filename: str) -> tuple[bool, str | None]:
    """
    解析单个文件：验证可读性 → 标记为已解析 → 清除旧索引 → 为整个知识库重建向量索引。
    返回 (成功, 错误信息)。
    """
    real = resolve_kb_folder_name(kb_name)
    if not real:
        return False, "知识库不存在"
    safe_name, err = safe_upload_basename(filename)
    if err:
        return False, err
    path = kb_dir(real) / safe_name
    if not path.is_file():
        return False, "文件不存在"

    try:
        from llama_index.core import SimpleDirectoryReader

        docs = SimpleDirectoryReader(input_files=[str(path)]).load_data()
    except Exception as e:
        msg = str(e) or "解析失败"
        set_file_parse_result(real, safe_name, parsed=False, error=msg)
        invalidate_kb_index_cache(real)
        return False, msg

    if not docs:
        msg = "未读取到文档内容"
        set_file_parse_result(real, safe_name, parsed=False, error=msg)
        invalidate_kb_index_cache(real)
        return False, msg

    texts = [(getattr(d, "text", None) or "").strip() for d in docs]
    if not any(texts):
        msg = "文档内容为空"
        set_file_parse_result(real, safe_name, parsed=False, error=msg)
        invalidate_kb_index_cache(real)
        return False, msg

    set_file_parse_result(
        real,
        safe_name,
        parsed=True,
        error=None,
        parsed_at=datetime.now(timezone.utc).isoformat(),
    )

    invalidate_kb_index_cache(real)

    idx = build_kb_index(real)
    if idx is None:
        return True, "文件已解析，但索引构建失败（检索可能不可用）"

    return True, None
