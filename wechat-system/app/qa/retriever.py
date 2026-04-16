import asyncio
import hashlib
from typing import Any, Dict, List, Optional

from app.qa.doc_processor import load_documents
from app.qa.ai_client import call_ai_api, embed_texts
from app.config import get_settings


try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models as qmodels
except Exception:
    QdrantClient = None
    qmodels = None


_index_lock = asyncio.Lock()
_index_ready = False
_qdrant_client: Optional["QdrantClient"] = None


def _chunk_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    text = text.strip()
    if not text:
        return []
    if chunk_size <= 0:
        return [text]
    overlap = max(0, min(overlap, chunk_size - 1)) if chunk_size > 1 else 0
    step = max(1, chunk_size - overlap)

    chunks: List[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start += step
    return chunks


def _point_id(source: str, chunk_index: int) -> str:
    raw = f"{source}#{chunk_index}".encode("utf-8")
    return hashlib.sha1(raw).hexdigest()


def _get_qdrant_client() -> "QdrantClient":
    global _qdrant_client
    if _qdrant_client is not None:
        return _qdrant_client
    settings = get_settings()
    if QdrantClient is None:
        raise RuntimeError("qdrant-client 未安装")
    _qdrant_client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key or None)
    return _qdrant_client


async def _run_blocking(fn, *args, **kwargs):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: fn(*args, **kwargs))


async def _ensure_index():
    global _index_ready
    if _index_ready:
        return

    async with _index_lock:
        if _index_ready:
            return

        settings = get_settings()
        documents = load_documents(settings.docs_path)
        if not documents:
            raise RuntimeError("知识库尚未配置")

        chunks: List[Dict[str, Any]] = []
        for doc in documents:
            source = str(doc.get("source") or "")
            content = str(doc.get("content") or "")
            for i, chunk in enumerate(_chunk_text(content, settings.qa_chunk_size, settings.qa_chunk_overlap)):
                chunks.append({"id": _point_id(source, i), "text": chunk, "source": source})

        if not chunks:
            raise RuntimeError("知识库为空")

        embeddings: List[List[float]] = []
        batch_size = 64
        for start in range(0, len(chunks), batch_size):
            batch = chunks[start : start + batch_size]
            vectors = await embed_texts([c["text"] for c in batch])
            embeddings.extend(vectors)

        vector_size = len(embeddings[0])

        def _sync_recreate_and_upsert():
            client = _get_qdrant_client()
            client.recreate_collection(
                collection_name=settings.qdrant_collection,
                vectors_config=qmodels.VectorParams(size=vector_size, distance=qmodels.Distance.COSINE),
            )
            points = [
                qmodels.PointStruct(
                    id=chunks[i]["id"],
                    vector=embeddings[i],
                    payload={"text": chunks[i]["text"], "source": chunks[i]["source"]},
                )
                for i in range(len(chunks))
            ]
            client.upsert(collection_name=settings.qdrant_collection, points=points)

        await _run_blocking(_sync_recreate_and_upsert)
        _index_ready = True


async def answer_question(question: str) -> str:
    settings = get_settings()
    documents = load_documents(settings.docs_path)
    if not documents:
        return "暂无法解答，知识库尚未配置。"

    fallback_context = "\n\n".join([str(doc.get("content") or "") for doc in documents]).strip()
    if not settings.qa_vector_enabled:
        return await call_ai_api(question, fallback_context)

    try:
        await _ensure_index()
        query_vector = (await embed_texts([question]))[0]

        def _sync_search():
            client = _get_qdrant_client()
            return client.search(
                collection_name=settings.qdrant_collection,
                query_vector=query_vector,
                limit=settings.qa_retrieval_top_k,
                with_payload=True,
            )

        hits = await _run_blocking(_sync_search)
        contexts: List[str] = []
        for hit in hits or []:
            payload = getattr(hit, "payload", None) or {}
            text = payload.get("text")
            source = payload.get("source")
            if isinstance(text, str) and text.strip():
                contexts.append(f"[{source}] {text}" if source else text)

        context = "\n\n".join(contexts).strip() or fallback_context
        return await call_ai_api(question, context)
    except Exception:
        return await call_ai_api(question, fallback_context)
