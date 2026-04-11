from typing import List, Dict, Optional
import httpx
from app.config import get_settings


async def call_ai_api(question: str, context: str) -> str:
    """
    调用 AI 接口进行问答。
    """
    settings = get_settings()
    if not settings.ai_enabled or not settings.ai_api_key:
        return "暂无法解答，AI 服务尚未配置。"

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
                return "暂无法解答，AI 响应格式异常。"
            
            content = choices[0].get("message", {}).get("content", "").strip()
            return content or "暂无法解答，AI 未能返回内容。"

    except httpx.HTTPError as e:
        return f"暂无法解答，网络错误: {str(e)}"
    except Exception as e:
        return f"暂无法解答，发生错误: {str(e)}"
