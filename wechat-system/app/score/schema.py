from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

from app.score.models import ScoreRecord


SCORE_RECORD_COLUMNS = {
    "id_card_suffix": "VARCHAR(4)",
    "class_name": "VARCHAR(64)",
    "total_rank": "INTEGER",
    "weighted_average_score": "FLOAT",
    "course_code": "VARCHAR(32)",
    "credit": "FLOAT",
    "course_order": "INTEGER",
}


def ensure_score_schema(engine: Engine) -> None:
    inspector = inspect(engine)
    if not inspector.has_table(ScoreRecord.__tablename__):
        return

    columns = {column["name"] for column in inspector.get_columns(ScoreRecord.__tablename__)}
    missing_columns = {
        name: column_type
        for name, column_type in SCORE_RECORD_COLUMNS.items()
        if name not in columns
    }
    if not missing_columns:
        return

    with engine.begin() as conn:
        for name, column_type in missing_columns.items():
            conn.execute(text(f"ALTER TABLE score_records ADD COLUMN {name} {column_type}"))
