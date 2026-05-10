import asyncio
import json
from typing import Any, List

import httpx
from app.config import get_settings

try:
    from tencentcloud.common import credential
    from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
    from tencentcloud.common.profile.client_profile import ClientProfile
    from tencentcloud.common.profile.http_profile import HttpProfile
    from tencentcloud.hunyuan.v20230901 import hunyuan_client, models as hunyuan_models
except Exception:
    credential = None
    TencentCloudSDKException = Exception
    ClientProfile = None
    HttpProfile = None
    hunyuan_client = None
    hunyuan_models = None


_QA_FALLBACK = "暂无法回答，请直接询问老师"
_UNCERTAIN_ANSWER_MARKERS = [
    "不知道",
    "无法回答",
    "无法解答",
    "暂无法",
    "不清楚",
    "无法根据",
    "无法查到",
    "无法提供",
    "没有相关信息",
    "没有提及",
    "未提及",
    "未提供",
    "没有说明",
]


def _normalize_answer(content: str) -> str:
    content = content.strip()
    if not content:
        return _QA_FALLBACK

    normalized = "".join(content.split())
    if any(marker in normalized for marker in _UNCERTAIN_ANSWER_MARKERS):
        return _QA_FALLBACK
    return content


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
        f"如果你无法根据【上下文】回答，只能回复“{_QA_FALLBACK}”，不要补充解释，不要编造答案。\n\n"
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
            
            content = choices[0].get("message", {}).get("content", "")
            return _normalize_answer(content)

    except httpx.HTTPError as e:
        return _QA_FALLBACK
    except Exception as e:
        return _QA_FALLBACK


async def embed_texts(texts: List[str]) -> List[List[float]]:
    settings = get_settings()
    if not settings.ai_enabled or not settings.tencent_secret_id or not settings.tencent_secret_key:
        raise RuntimeError(_QA_FALLBACK)
    if not texts:
        return []
    if credential is None or ClientProfile is None or HttpProfile is None or hunyuan_client is None or hunyuan_models is None:
        raise RuntimeError("tencentcloud-sdk-python-hunyuan 未安装")

    def _get_item_value(item: Any, name: str):
        if isinstance(item, dict):
            return item.get(name) or item.get(name[:1].lower() + name[1:])
        return getattr(item, name, None) or getattr(item, name[:1].lower() + name[1:], None)

    def _sync_get_embeddings():
        cred = credential.Credential(settings.tencent_secret_id, settings.tencent_secret_key)
        http_profile = HttpProfile()
        http_profile.endpoint = settings.tencent_embedding_endpoint
        http_profile.reqTimeout = settings.ai_timeout_sec

        client_profile = ClientProfile()
        client_profile.httpProfile = http_profile

        client = hunyuan_client.HunyuanClient(cred, settings.tencent_region, client_profile)
        req = hunyuan_models.GetEmbeddingRequest()
        req.from_json_string(json.dumps({"InputList": texts}, ensure_ascii=False))
        return client.GetEmbedding(req)

    try:
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(None, _sync_get_embeddings)
    except TencentCloudSDKException as e:
        raise RuntimeError(_QA_FALLBACK) from e

    items = getattr(response, "Data", None) or []
    if not isinstance(items, list) or not items:
        raise RuntimeError(_QA_FALLBACK)

    indexed_items = []
    for position, item in enumerate(items):
        index = _get_item_value(item, "Index")
        indexed_items.append((index if isinstance(index, int) else position, item))
    indexed_items.sort(key=lambda pair: pair[0])

    embeddings: List[List[float]] = []
    for _, item in indexed_items:
        emb = _get_item_value(item, "Embedding")
        if not isinstance(emb, list) or not emb:
            raise RuntimeError(_QA_FALLBACK)
        embeddings.append(emb)

    if len(embeddings) != len(texts):
        raise RuntimeError(_QA_FALLBACK)
    return embeddings
