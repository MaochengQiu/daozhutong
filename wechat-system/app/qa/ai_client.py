from typing import List, Dict

import requests

from app.config import get_settings


class AIClient:
    def __init__(self):
        self.settings = get_settings()

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        if not self.settings.ai_enabled or not self.settings.ai_api_key:
            return "暂无法解答"

        url = f"{self.settings.ai_api_base.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.settings.ai_api_key}",
            "Content-Type": "application/json",
        }
        payload: Dict[str, object] = {
            "model": self.settings.ai_chat_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.1,
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=self.settings.ai_timeout_sec)
        resp.raise_for_status()
        data = resp.json()
        choices: List[dict] = data.get("choices", [])
        if not choices:
            return "暂无法解答"
        return choices[0].get("message", {}).get("content", "").strip() or "暂无法解答"


class QAService:
    def __init__(self, chunks, retriever, ai_client):
        self.chunks = chunks
        self.retriever = retriever
        self.ai_client = ai_client
        self.settings = get_settings()

    def answer(self, question: str) -> str:
        ranked = self.retriever.search(question, top_k=self.settings.qa_top_k)
        if not ranked:
            return "暂无法解答"

        best_score = ranked[0][1]
        if best_score < self.settings.qa_relevance_threshold:
            return "暂无法解答"

        context_chunks = [chunk for chunk, score in ranked if score >= self.settings.qa_relevance_threshold]
        if not context_chunks:
            return "暂无法解答"

        context = "\n".join([f"- {ch.answer or ch.text}" for ch in context_chunks[: self.settings.qa_top_k]])
        prompt = (
            f"用户问题：{question}\n"
            f"知识库内容：\n{context}\n\n"
            "请仅依据知识库内容回答。如果无法从知识库明确得出答案，只回复：暂无法解答。"
        )
        sys_prompt = "你是一个严格依据给定文档回答问题的助手，禁止使用外部知识。"
        try:
            result = self.ai_client.chat(sys_prompt, prompt)
        except Exception:
            return "暂无法解答"
        return result if result else "暂无法解答"
