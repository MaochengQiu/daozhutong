import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.database import Base, SessionLocal, engine
from app.score.models import ScoreRecord


def init_db():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        existing = session.query(ScoreRecord).count()
        if existing == 0:
            session.add_all(
                [
                    ScoreRecord(student_id="25000000001", name="张三", course="数学", score=92),
                    ScoreRecord(student_id="25000000001", name="张三", course="英语", score=88),
                    ScoreRecord(student_id="25000000002", name="李四", course="数学", score=79),
                    ScoreRecord(student_id="25000000002", name="李四", course="英语", score=85),
                ]
            )
            session.commit()
    finally:
        session.close()


if __name__ == "__main__":
    init_db()
    print("database initialized")
