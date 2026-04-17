from typing import List, Dict, Optional
import httpx
from app.config import get_settings


_QA_FALLBACK = "暂无法回答，请直接询问老师"


async def call_ai_api(question: str, context: str) -> str:
    """
    调用 AI 接口进行问答。
    """
    settings = get_settings()
    if not settings.ai_enabled or not settings.ai_api_key:
        return _QA_FALLBACK

    url = f"{settings.ai_api_base.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.ai_api_key}",
        "Content-Type": "application/json",
    }

    system_prompt = (
        "你是一个校园助手。请基于提供的【上下文】回答用户提出的【问题】。\n"
        "如果你无法根据【上下文】回答，请直接告知用户你不知道，不要编造答案。\n\n"
        f"【上下文】：\n{context}"
    )

    payload = {
        "model": settings.ai_chat_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ],
        "temperature": 0.3,
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url,
                headers=headers,
                json=payload,
                timeout=settings.ai_timeout_sec
            )
            resp.raise_for_status()
            data = resp.json()
            choices = data.get("choices", [])
            if not choices:
                return _QA_FALLBACK
            
            content = choices[0].get("message", {}).get("content", "").strip()
            if not content:
                return _QA_FALLBACK
            lowered = content.replace(" ", "")
            if len(lowered) <= 80 and any(k in lowered for k in ["不知道", "无法回答", "无法解答", "暂无法", "不清楚", "无法根据"]):
                return _QA_FALLBACK
            return content

    except httpx.HTTPError as e:
        return _QA_FALLBACK
    except Exception as e:
        return _QA_FALLBACK


async def embed_texts(texts: List[str]) -> List[List[float]]:
    settings = get_settings()
    if not settings.ai_enabled or not settings.ai_api_key:
        raise RuntimeError(_QA_FALLBACK)
    if not texts:
        return []

    url = f"{settings.ai_api_base.rstrip('/')}/embeddings"
    headers = {
        "Authorization": f"Bearer {settings.ai_api_key}",
        "Content-Type": "application/json",
    }
    payload = {"model": settings.ai_embedding_model, "input": texts}

    async with httpx.AsyncClient() as client:
        resp = await client.post(url, headers=headers, json=payload, timeout=settings.ai_timeout_sec)
        resp.raise_for_status()
        data = resp.json()

    items = data.get("data", [])
    if not isinstance(items, list) or not items:
        raise RuntimeError(_QA_FALLBACK)

    embeddings: List[List[float]] = []
    for item in items:
        emb = item.get("embedding")
        if not isinstance(emb, list) or not emb:
            raise RuntimeError(_QA_FALLBACK)
        embeddings.append(emb)

    if len(embeddings) != len(texts):
        raise RuntimeError(_QA_FALLBACK)
    return embeddings
