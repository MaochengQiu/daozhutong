from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.score.models import ScoreRecord


@dataclass
class ScoreImportResult:
    imported: int
    skipped: int
    sheets: int


_REQUIRED_FIELDS = {"student_id", "name", "id_card_suffix", "course", "score"}
_HEADER_ALIASES = {
    "student_id": ["student_id", "studentid", "学号", "学生学号", "学生编号", "考号"],
    "name": ["name", "姓名", "学生姓名"],
    "id_card_suffix": [
        "id_card_suffix",
        "idcardsuffix",
        "身份证后6位",
        "身份证后六位",
        "身份证号后6位",
        "身份证号码后6位",
        "证件号后6位",
        "身份证号",
        "身份证号码",
        "证件号",
    ],
    "course": ["course", "课程", "课程名称", "课程名", "科目", "考试科目"],
    "score": ["score", "成绩", "分数", "得分"],
}


def _normalize_header(value: Any) -> str:
    return (
        str(value or "")
        .strip()
        .lower()
        .replace(" ", "")
        .replace("_", "")
        .replace("-", "")
        .replace("：", "")
        .replace(":", "")
    )


_HEADER_TO_FIELD = {
    _normalize_header(alias): field
    for field, aliases in _HEADER_ALIASES.items()
    for alias in aliases
}


def _cell_to_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def _id_card_suffix(value: Any) -> str:
    text = _cell_to_text(value)
    digits = "".join(ch for ch in text if ch.isdigit())
    if not digits:
        return ""
    if len(digits) < 6:
        return digits.zfill(6)
    return digits[-6:]


def _score_to_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace("%", "")
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _header_map(row: tuple[Any, ...]) -> Dict[int, str]:
    mapping: Dict[int, str] = {}
    for index, value in enumerate(row):
        field = _HEADER_TO_FIELD.get(_normalize_header(value))
        if field and field not in mapping.values():
            mapping[index] = field
    return mapping


def _record_from_row(row: tuple[Any, ...], mapping: Dict[int, str]) -> Optional[ScoreRecord]:
    values = {
        field: row[index] if index < len(row) else None
        for index, field in mapping.items()
    }

    student_id = _cell_to_text(values.get("student_id"))
    name = _cell_to_text(values.get("name"))
    id_card_suffix = _id_card_suffix(values.get("id_card_suffix"))
    course = _cell_to_text(values.get("course"))
    score = _score_to_float(values.get("score"))

    if not student_id or not name or len(id_card_suffix) != 6 or not course or score is None:
        return None

    return ScoreRecord(
        student_id=student_id,
        name=name,
        id_card_suffix=id_card_suffix,
        course=course,
        score=score,
    )


def load_score_records_from_xlsx(xlsx_path: str) -> tuple[List[ScoreRecord], int, int]:
    try:
        from openpyxl import load_workbook
    except ImportError as exc:
        raise RuntimeError("openpyxl 未安装，无法导入 .xlsx 成绩单") from exc

    path = Path(xlsx_path)
    if path.suffix.lower() != ".xlsx":
        raise ValueError("仅支持 .xlsx 成绩单")
    if not path.exists():
        raise FileNotFoundError(f"成绩单不存在: {path}")

    workbook = load_workbook(path, read_only=True, data_only=True)
    records: List[ScoreRecord] = []
    skipped = 0

    try:
        for sheet in workbook.worksheets:
            mapping: Optional[Dict[int, str]] = None
            for row_index, row in enumerate(sheet.iter_rows(values_only=True), start=1):
                if mapping is None:
                    candidate = _header_map(row)
                    if _REQUIRED_FIELDS.issubset(set(candidate.values())):
                        mapping = candidate
                    elif row_index >= 20:
                        break
                    continue

                record = _record_from_row(row, mapping)
                if record is None:
                    if any(value not in (None, "") for value in row):
                        skipped += 1
                    continue
                records.append(record)
    finally:
        workbook.close()

    return records, skipped, len(workbook.worksheets)


def import_scores_from_xlsx(db: Session, xlsx_path: str, replace: bool = False) -> ScoreImportResult:
    records, skipped, sheets = load_score_records_from_xlsx(xlsx_path)

    if replace:
        db.query(ScoreRecord).delete()

    for record in records:
        db.query(ScoreRecord).filter(
            ScoreRecord.student_id == record.student_id,
            ScoreRecord.name == record.name,
            ScoreRecord.id_card_suffix == record.id_card_suffix,
            ScoreRecord.course == record.course,
        ).delete(synchronize_session=False)
        db.add(record)

    db.commit()
    return ScoreImportResult(imported=len(records), skipped=skipped, sheets=sheets)
