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
                    ScoreRecord(student_id="2026001", name="张三", course="数学", score=92),
                    ScoreRecord(student_id="2026001", name="张三", course="英语", score=88),
                    ScoreRecord(student_id="2026002", name="李四", course="数学", score=79),
                    ScoreRecord(student_id="2026002", name="李四", course="英语", score=85),
                ]
            )
            session.commit()
    finally:
        session.close()


if __name__ == "__main__":
    init_db()
    print("database initialized")
