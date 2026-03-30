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


class ScoreQueryRequest(BaseModel):
    student_id: str = Field(min_length=2, max_length=32)
    name: str = Field(min_length=1, max_length=64)

    @field_validator("student_id", "name")
    @classmethod
    def no_whitespace_only(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("字段不能为空")
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

    records = ScoreService.query_personal_scores(db, payload.student_id, payload.name)
    if not records:
        return {"ok": False, "message": "未查询到成绩，请核对学号和姓名"}

    return {
        "ok": True,
        "data": [
            {"course": r.course, "score": r.score}
            for r in records
        ],
    }
