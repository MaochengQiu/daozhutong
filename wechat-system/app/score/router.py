import time
from collections import defaultdict, deque
from typing import Deque, Dict

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db_session
from app.score.service import ScoreService


router = APIRouter(prefix="/api/score")
settings = get_settings()
_rate_window: Dict[str, Deque[float]] = defaultdict(deque)
INPUT_MISMATCH_MESSAGE = "输入信息有误，请重新输入"


class ScoreQueryRequest(BaseModel):
    student_id: str = Field(min_length=2, max_length=32)
    name: str = Field(min_length=1, max_length=64)
    id_card_suffix: str = Field(pattern=r"^[0-9Xx]{4}$")

    @field_validator("student_id", "name")
    @classmethod
    def no_whitespace_only(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("字段不能为空")
        return v

    @field_validator("id_card_suffix")
    @classmethod
    def valid_id_card_suffix(cls, v: str) -> str:
        v = v.strip().upper()
        if len(v) != 4 or any(ch not in "0123456789X" for ch in v):
            raise ValueError("身份证后4位必须为4位数字或X")
        return v


def _check_rate_limit(ip: str):
    now = time.time()
    window = _rate_window[ip]
    while window and now - window[0] > 60:
        window.popleft()
    if len(window) >= settings.score_rate_limit_per_minute:
        raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试")
    window.append(now)


@router.post("/query")
def query_score(payload: ScoreQueryRequest, request: Request, db: Session = Depends(get_db_session)):
    client_ip = request.client.host if request.client else "unknown"
    _check_rate_limit(client_ip)

    records = ScoreService.query_personal_scores(db, payload.student_id, payload.name, payload.id_card_suffix)
    if not records:
        return {"ok": False, "message": INPUT_MISMATCH_MESSAGE}

    return {
        "ok": True,
        "summary": ScoreService.build_summary(records),
        "data": [
            {
                "course": r.course,
                "course_code": r.course_code,
                "credit": r.credit,
                "score": r.score,
            }
            for r in records
        ],
    }
