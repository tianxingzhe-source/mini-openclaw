"""RAG 检索工具 - LlamaIndex 向量检索 + BM25 混合检索（多知识库，仅已解析文件入索引）"""

from pathlib import Path

from langchain_core.tools import tool

from config import KNOWLEDGE_DIR, STORAGE_DIR, OPENAI_API_KEY, OPENAI_BASE_URL, EMBEDDING_MODEL
from knowledge_store import list_parsed_absolute_paths

_index_cache: dict[str, object] = {}
_fusion_cache: dict[str, object] = {}
_embed_configured = False

CHUNK_SIZE = 512
CHUNK_OVERLAP = 64


def _ensure_embed_settings() -> bool:
    """初始化嵌入模型。使用 openai SDK 直接调用，兼容任意 OpenAI 兼容 API。"""
    global _embed_configured
    if _embed_configured:
        return True
    try:
        import openai
        from llama_index.core import Settings
        from llama_index.core.embeddings import BaseEmbedding
        from pydantic import PrivateAttr

        class _OpenAICompatEmbedding(BaseEmbedding):
            _client: object = PrivateAttr(default=None)
            _model_id: str = PrivateAttr(default="")

            def __init__(self, model: str, api_key: str, api_base: str, **kwargs):
                super().__init__(**kwargs)
                self._client = openai.OpenAI(api_key=api_key, base_url=api_base)
                self._model_id = model

            def _get_query_embedding(self, query: str) -> list[float]:
                resp = self._client.embeddings.create(input=[query], model=self._model_id)
                return resp.data[0].embedding

            def _get_text_embedding(self, text: str) -> list[float]:
                resp = self._client.embeddings.create(input=[text], model=self._model_id)
                return resp.data[0].embedding

            async def _aget_query_embedding(self, query: str) -> list[float]:
                return self._get_query_embedding(query)

            def _get_text_embeddings(self, texts: list[str]) -> list[list[float]]:
                resp = self._client.embeddings.create(input=texts, model=self._model_id)
                return [d.embedding for d in sorted(resp.data, key=lambda x: x.index)]

        Settings.embed_model = _OpenAICompatEmbedding(
            model=EMBEDDING_MODEL,
            api_key=OPENAI_API_KEY,
            api_base=OPENAI_BASE_URL,
        )
        _embed_configured = True
        print(f"[RAG] 嵌入模型初始化成功: {EMBEDDING_MODEL}")
        return True
    except ImportError as e:
        print(f"[RAG] LlamaIndex 依赖缺失: {e}")
        return False
    except Exception as e:
        print(f"[RAG] 嵌入模型初始化失败: {e}")
        return False


def _get_sentence_splitter():
    from llama_index.core.node_parser import SentenceSplitter
    return SentenceSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)


def list_kb_folder_names() -> list[str]:
    if not KNOWLEDGE_DIR.exists():
        return []
    return sorted(
        p.name
        for p in KNOWLEDGE_DIR.iterdir()
        if p.is_dir() and not p.name.startswith(".")
    )


def invalidate_kb_index_cache(kb_name: str) -> None:
    """文件或解析状态变更后丢弃内存缓存并删除该库的持久化索引。"""
    import shutil

    _index_cache.pop(kb_name, None)
    _fusion_cache.pop(kb_name, None)
    persist = STORAGE_DIR / "index" / kb_name
    if persist.exists():
        shutil.rmtree(persist, ignore_errors=True)


def _persist_dir_for_kb(kb_name: str) -> str:
    return str(STORAGE_DIR / "index" / kb_name)


def build_kb_index(kb_name: str):
    """为指定知识库的所有已解析文件构建向量索引，分块、嵌入并持久化到磁盘。

    解析完成后调用此函数，确保索引立即可用于检索。
    返回构建好的 VectorStoreIndex 或 None。
    """
    if not _ensure_embed_settings():
        return None

    try:
        from llama_index.core import VectorStoreIndex, SimpleDirectoryReader

        parsed_paths = list_parsed_absolute_paths(kb_name)
        if not parsed_paths:
            print(f"[RAG] 知识库 '{kb_name}' 无已解析文件，跳过索引构建")
            return None

        input_files = [str(p) for p in parsed_paths]
        documents = SimpleDirectoryReader(input_files=input_files).load_data()
        if not documents:
            print(f"[RAG] 知识库 '{kb_name}' 文档加载为空，跳过索引构建")
            return None

        splitter = _get_sentence_splitter()
        nodes = splitter.get_nodes_from_documents(documents)
        if not nodes:
            print(f"[RAG] 知识库 '{kb_name}' 分块后无节点，跳过索引构建")
            return None

        print(f"[RAG] 知识库 '{kb_name}': {len(documents)} 个文档 → {len(nodes)} 个分块，正在构建向量索引…")
        idx = VectorStoreIndex(nodes)

        persist_dir = _persist_dir_for_kb(kb_name)
        Path(persist_dir).mkdir(parents=True, exist_ok=True)
        idx.storage_context.persist(persist_dir=persist_dir)

        _index_cache[kb_name] = idx
        _fusion_cache.pop(kb_name, None)

        print(f"[RAG] 知识库 '{kb_name}' 索引构建完成，已持久化至 {persist_dir}")
        return idx

    except Exception as e:
        print(f"[RAG] 索引构建失败 ({kb_name}): {e}")
        import traceback
        traceback.print_exc()
        return None


def _hybrid_retrieve(kb_name: str, index, query: str, similarity_top_k: int):
    """同一知识库：向量检索 + BM25 手动融合（相对分数归一化后求和）。"""
    from llama_index.retrievers.bm25 import BM25Retriever

    if kb_name not in _fusion_cache:
        _fusion_cache[kb_name] = {
            "vector": index.as_retriever(similarity_top_k=similarity_top_k),
            "bm25": BM25Retriever.from_defaults(
                index=index,
                similarity_top_k=similarity_top_k,
                skip_stemming=True,
            ),
        }

    retrievers = _fusion_cache[kb_name]
    vector_nodes = retrievers["vector"].retrieve(query)
    bm25_nodes = retrievers["bm25"].retrieve(query)

    merged: dict[str, tuple[float, object]] = {}
    for nodes in [vector_nodes, bm25_nodes]:
        if not nodes:
            continue
        max_score = max((abs(n.score) for n in nodes if n.score is not None), default=1.0) or 1.0
        for n in nodes:
            norm_score = (n.score or 0.0) / max_score
            nid = n.node.node_id
            if nid in merged:
                merged[nid] = (merged[nid][0] + norm_score, merged[nid][1])
            else:
                merged[nid] = (norm_score, n)

    ranked = sorted(merged.values(), key=lambda x: -x[0])
    results = []
    for combined_score, node in ranked[:similarity_top_k]:
        node.score = combined_score
        results.append(node)
    return results


def _build_or_load_index_for_kb(kb_name: str):
    """单个知识库：加载持久化索引或回退构建。"""
    if kb_name in _index_cache:
        return _index_cache[kb_name]

    if not _ensure_embed_settings():
        return None

    try:
        from llama_index.core import StorageContext, load_index_from_storage

        kb_path = KNOWLEDGE_DIR / kb_name
        if not kb_path.is_dir():
            return None

        parsed_paths = list_parsed_absolute_paths(kb_name)
        if not parsed_paths:
            return None

        persist_dir = _persist_dir_for_kb(kb_name)
        persist_path = Path(persist_dir)

        if persist_path.exists() and any(persist_path.iterdir()):
            storage_context = StorageContext.from_defaults(persist_dir=persist_dir)
            idx = load_index_from_storage(storage_context)
            _index_cache[kb_name] = idx
            return idx

        return build_kb_index(kb_name)

    except Exception as e:
        print(f"[RAG] 索引加载失败 ({kb_name}): {e}")
        return None


def _retrieve_all_kbs(query: str, top_k_per_kb: int = 5, final_top_k: int = 5):
    scored = []
    for kb in list_kb_folder_names():
        idx = _build_or_load_index_for_kb(kb)
        if idx is None:
            continue
        try:
            nodes = _hybrid_retrieve(kb, idx, query, top_k_per_kb)
        except Exception as e:
            print(f"[RAG] 混合检索失败 ({kb}): {e}")
            continue
        for node in nodes:
            score = float(node.score) if node.score is not None else 0.0
            scored.append((score, kb, node))

    scored.sort(key=lambda x: -x[0])
    return scored[:final_top_k]


def create_rag_search_tool():
    @tool("search_knowledge_base")
    def search_knowledge_base(query: str) -> str:
        """在知识库中进行混合检索（向量检索 + BM25 关键词匹配）。
        当用户询问具体的知识库内容（非对话历史）时使用此工具。
        仅包含前端已「解析」的 .md、.txt、.pdf 文件。

        Args:
            query: 检索查询语句
        """
        kbs = list_kb_folder_names()
        if not kbs:
            return (
                "暂无知识库。请在前端「知识库」中创建知识库、上传文件并完成解析。"
            )

        try:
            ranked = _retrieve_all_kbs(query)
            if not ranked:
                return (
                    f"未在知识库中找到与 '{query}' 相关的内容。"
                    "请确认已有文件完成解析（未解析的文件不参与检索）。"
                )

            results = []
            for i, (score, kb, node) in enumerate(ranked, 1):
                score_s = f" (相关度: {score:.3f})" if score else ""
                source = node.metadata.get("file_name", "未知来源")
                text = node.get_text().strip()
                if len(text) > 1000:
                    text = text[:1000] + "..."
                results.append(
                    f"### 结果 {i}{score_s}\n**知识库**: {kb}\n**来源**: {source}\n\n{text}"
                )

            return "\n\n---\n\n".join(results)

        except Exception as e:
            return f"⚠️ 检索失败: {str(e)}"

    return search_knowledge_base
