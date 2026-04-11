from pathlib import Path
from typing import List, Dict


def load_documents(docs_dir: str) -> List[Dict[str, str]]:
    """
    加载指定目录下的所有文档内容。
    假设文档为文本格式。
    """
    docs_path = Path(docs_dir)
    if not docs_path.exists():
        return []

    documents = []
    # 如果 docs_path 是一个文件，则直接读取
    if docs_path.is_file():
        content = docs_path.read_text(encoding="utf-8").strip()
        if content:
            documents.append({"content": content, "source": docs_path.name})
    else:
        # 如果是目录，则遍历
        for file in docs_path.glob("*.txt"):
            content = file.read_text(encoding="utf-8").strip()
            if content:
                documents.append({"content": content, "source": file.name})

    return documents
