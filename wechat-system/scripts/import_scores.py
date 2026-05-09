import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.database import Base, SessionLocal, engine
from app.score.importer import import_scores_from_xlsx
from app.score.models import ScoreRecord


def main():
    parser = argparse.ArgumentParser(description="Import score records from an .xlsx file.")
    parser.add_argument("xlsx_path", help="Path to the .xlsx score file")
    parser.add_argument("--replace", action="store_true", help="Delete existing score records before importing")
    args = parser.parse_args()

    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        result = import_scores_from_xlsx(session, args.xlsx_path, replace=args.replace)
    finally:
        session.close()

    print(f"sheets={result.sheets}")
    print(f"imported={result.imported}")
    print(f"skipped={result.skipped}")


if __name__ == "__main__":
    main()
