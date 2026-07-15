import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.database import Base, SessionLocal, engine
from app.score.importer import import_scores_from_xlsx
from app.score.schema import ensure_score_schema
DEFAULT_DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DEFAULT_IDENTITY_PATH = DEFAULT_DATA_DIR / "20250822 新生基本信息.xlsx"


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


def _resolve_identity_xlsx_path(identity_xlsx_path: str | None) -> str | None:
    if identity_xlsx_path:
        return identity_xlsx_path
    if DEFAULT_IDENTITY_PATH.exists():
        return str(DEFAULT_IDENTITY_PATH)
    return None


def main():
    parser = argparse.ArgumentParser(description="Import score records from an .xlsx file.")
    parser.add_argument("xlsx_path", nargs="?", help="Path to the .xlsx score file")
    parser.add_argument("--identity-xlsx", help="Optional student identity .xlsx used to fill id_card_suffix")
    parser.add_argument("--replace", action="store_true", help="Delete existing score records before importing")
    args = parser.parse_args()
    xlsx_path = _resolve_xlsx_path(args.xlsx_path)
    identity_xlsx_path = _resolve_identity_xlsx_path(args.identity_xlsx)

    Base.metadata.create_all(bind=engine)
    ensure_score_schema(engine)
    session = SessionLocal()
    try:
        result = import_scores_from_xlsx(
            session,
            xlsx_path,
            replace=args.replace,
            identity_xlsx_path=identity_xlsx_path,
        )
    finally:
        session.close()

    print(f"xlsx_path={xlsx_path}")
    print(f"identity_xlsx_path={identity_xlsx_path or ''}")
    print(f"sheets={result.sheets}")
    print(f"imported={result.imported}")
    print(f"skipped={result.skipped}")


if __name__ == "__main__":
    main()
