from fastapi import APIRouter
from pydantic import BaseModel, Field, field_validator

from app.qa.retriever import answer_question


router = APIRouter(prefix="/api/qa")


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)

    @field_validator("question")
    @classmethod
    def not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("字段不能为空")
        return v


@router.post("/ask")
async def ask(payload: AskRequest):
    answer = await answer_question(payload.question)
    return {"ok": True, "answer": answer}

