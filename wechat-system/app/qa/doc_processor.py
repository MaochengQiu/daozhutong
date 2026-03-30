from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class DocChunk:
    chunk_id: str
    question: str
    answer: str
    text: str


class DocProcessor:
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)

    def load_chunks(self) -> List[DocChunk]:
        if not self.file_path.exists():
            return []

        raw = self.file_path.read_text(encoding="utf-8").strip()
        if not raw:
            return []

        blocks = [blk.strip() for blk in raw.split("\n\n") if blk.strip()]
        chunks: List[DocChunk] = []
        for idx, block in enumerate(blocks):
            question = ""
            answer = ""
            lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
            for line in lines:
                if line.startswith(("Q:", "Q：", "问题:", "问题：")):
                    question = line.split(":", 1)[-1].strip() if ":" in line else line.split("：", 1)[-1].strip()
                elif line.startswith(("A:", "A：", "答案:", "答案：")):
                    answer = line.split(":", 1)[-1].strip() if ":" in line else line.split("：", 1)[-1].strip()

            if not answer and lines:
                answer = " ".join(lines)
            text = f"{question} {answer}".strip()
            chunks.append(
                DocChunk(
                    chunk_id=f"chunk-{idx}",
                    question=question,
                    answer=answer,
                    text=text,
                )
            )
        return chunks
