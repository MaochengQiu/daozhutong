from typing import List

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.score.models import ScoreRecord


class ScoreService:
    @staticmethod
    def query_personal_scores(db: Session, student_id: str, name: str) -> List[ScoreRecord]:
        stmt = (
            select(ScoreRecord)
            .where(ScoreRecord.student_id == student_id.strip())
            .where(ScoreRecord.name == name.strip())
            .order_by(ScoreRecord.course.asc())
        )
        return list(db.execute(stmt).scalars().all())
