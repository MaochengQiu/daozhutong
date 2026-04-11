from app.qa.doc_processor import load_documents
from app.qa.ai_client import call_ai_api
from app.config import get_settings


async def answer_question(question: str) -> str:
    """
    直接全文注入方式回答问题。
    """
    settings = get_settings()
    # 假设 docs_path 指向文件或目录
    documents = load_documents(settings.docs_path)
    
    if not documents:
        return "暂无法解答，知识库尚未配置。"
        
    # 直接拼接全文
    context = "\n\n".join([doc["content"] for doc in documents])
    
    # 限制上下文长度（如果需要）
    # 如果 context 过长（例如超过 8000 token），此处可根据具体模型做截断处理。
    # 根据用户说法，全量通常在 5 万字以内，对于一些长上下文模型是足够的。
    
    return await call_ai_api(question, context)
