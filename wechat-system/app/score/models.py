from sqlalchemy import Column, Float, String, Integer

from app.database import Base


class ScoreRecord(Base):
    __tablename__ = "score_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String(32), index=True)
    name = Column(String(64), index=True)
    course = Column(String(64))
    score = Column(Float)
