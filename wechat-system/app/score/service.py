from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.score.models import ScoreRecord


class ScoreService:
    @staticmethod
    def query_personal_scores(db: Session, student_id: str, name: str, id_card_suffix: str) -> List[ScoreRecord]:
        stmt = (
            select(ScoreRecord)
            .where(ScoreRecord.student_id == student_id.strip())
            .where(ScoreRecord.name == name.strip())
            .where(ScoreRecord.id_card_suffix == id_card_suffix.strip())
            .order_by(ScoreRecord.course_order.is_(None), ScoreRecord.course_order.asc(), ScoreRecord.course.asc())
        )
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def build_summary(records: List[ScoreRecord]) -> Optional[Dict[str, Any]]:
        if not records:
            return None
        first = records[0]
        return {
            "student_id": first.student_id,
            "name": first.name,
            "class_name": first.class_name,
            "weighted_average_score": first.weighted_average_score,
            "total_rank": first.total_rank,
        }
