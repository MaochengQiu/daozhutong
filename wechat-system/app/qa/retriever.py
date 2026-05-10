import asyncio
import uuid
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
_QA_FALLBACK = "暂无法回答，请直接询问老师"


def _chunk_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    text = text.strip()
    if not text:
        return []

    chunks: List[str] = []
    current: List[str] = []
    has_answer = False
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            if current:
                current.append("")
            continue

        normalized = line.lstrip()
        is_question = normalized.startswith(("Q:", "Q："))
        is_answer = normalized.startswith(("A:", "A："))

        if is_question and current and has_answer:
            chunk = "\n".join(current).strip()
            if chunk:
                chunks.append(chunk)
            current = []
            has_answer = False

        current.append(line)
        if is_answer:
            has_answer = True

    if current and has_answer:
        chunk = "\n".join(current).strip()
        if chunk:
            chunks.append(chunk)

    if chunks:
        return chunks

    if chunk_size <= 0:
        return [text]
    overlap = max(0, min(overlap, chunk_size - 1)) if chunk_size > 1 else 0
    step = max(1, chunk_size - overlap)

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
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{source}#{chunk_index}"))


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
        batch_size = 50
        for start in range(0, len(chunks), batch_size):
            batch = chunks[start : start + batch_size]
            vectors = await embed_texts([c["text"] for c in batch])
            embeddings.extend(vectors)

        vector_size = len(embeddings[0])

        def _sync_ensure_collection_and_upsert():
            client = _get_qdrant_client()

            def _current_vector_size():
                try:
                    info = client.get_collection(settings.qdrant_collection)
                    vectors = info.config.params.vectors
                    return getattr(vectors, "size", None)
                except Exception:
                    return None

            current_size = _current_vector_size()
            if current_size != vector_size:
                if client.collection_exists(settings.qdrant_collection):
                    client.delete_collection(settings.qdrant_collection)
                try:
                    client.create_collection(
                        collection_name=settings.qdrant_collection,
                        vectors_config=qmodels.VectorParams(size=vector_size, distance=qmodels.Distance.COSINE),
                    )
                except Exception:
                    if _current_vector_size() != vector_size:
                        raise

            points = [
                qmodels.PointStruct(
                    id=chunks[i]["id"],
                    vector=embeddings[i],
                    payload={"text": chunks[i]["text"], "source": chunks[i]["source"]},
                )
                for i in range(len(chunks))
            ]
            client.upsert(collection_name=settings.qdrant_collection, points=points)

        await _run_blocking(_sync_ensure_collection_and_upsert)
        _index_ready = True


async def answer_question(question: str) -> str:
    settings = get_settings()
    documents = load_documents(settings.docs_path)
    if not documents:
        return _QA_FALLBACK

    fallback_context = "\n\n".join([str(doc.get("content") or "") for doc in documents]).strip()
    if not settings.qa_vector_enabled:
        return await call_ai_api(question, fallback_context)

    try:
        await _ensure_index()
        query_vector = (await embed_texts([question]))[0]

        def _sync_search():
            client = _get_qdrant_client()
            result = client.query_points(
                collection_name=settings.qdrant_collection,
                query=query_vector,
                limit=settings.qa_retrieval_top_k,
                with_payload=True,
            )
            return getattr(result, "points", result)

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
