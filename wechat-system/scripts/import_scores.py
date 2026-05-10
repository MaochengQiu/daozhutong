import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.database import Base, SessionLocal, engine
from app.score.importer import import_scores_from_xlsx
DEFAULT_DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def _resolve_xlsx_path(xlsx_path: str | None) -> str:
    if xlsx_path:
        return xlsx_path

    candidates = sorted(path for path in DEFAULT_DATA_DIR.glob("*.xlsx") if path.is_file())
    if not candidates:
        raise FileNotFoundError(f"未在 {DEFAULT_DATA_DIR} 找到 .xlsx 成绩单")
    if len(candidates) > 1:
        names = ", ".join(path.name for path in candidates)
        raise RuntimeError(f"data 目录下存在多个 .xlsx 文件，请指定其中一个: {names}")
    return str(candidates[0])


def main():
    parser = argparse.ArgumentParser(description="Import score records from an .xlsx file.")
    parser.add_argument("xlsx_path", nargs="?", help="Path to the .xlsx score file")
    parser.add_argument("--replace", action="store_true", help="Delete existing score records before importing")
    args = parser.parse_args()
    xlsx_path = _resolve_xlsx_path(args.xlsx_path)

    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        result = import_scores_from_xlsx(session, xlsx_path, replace=args.replace)
    finally:
        session.close()

    print(f"xlsx_path={xlsx_path}")
    print(f"sheets={result.sheets}")
    print(f"imported={result.imported}")
    print(f"skipped={result.skipped}")


if __name__ == "__main__":
    main()
