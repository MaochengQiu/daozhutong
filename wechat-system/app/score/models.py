from sqlalchemy import Column, Float, String, Integer

from app.database import Base


class ScoreRecord(Base):
    __tablename__ = "score_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String(32), index=True)
    name = Column(String(64), index=True)
    id_card_suffix = Column(String(4), index=True)
    class_name = Column(String(64))
    total_rank = Column(Integer)
    weighted_average_score = Column(Float)
    course = Column(String(64))
    course_code = Column(String(32))
    credit = Column(Float)
    course_order = Column(Integer)
    score = Column(Float)
