import hashlib
import xml.etree.ElementTree as ET

from fastapi import APIRouter, Request, Response

from app.config import get_settings
from app.qa import AIClient, DocProcessor, QAService, Retriever
from app.wechat.reply import text_reply


router = APIRouter()
settings = get_settings()

chunks = DocProcessor(settings.docs_path).load_chunks()
retriever = Retriever(chunks)
qa_service = QAService(chunks=chunks, retriever=retriever, ai_client=AIClient())


def _verify_signature(signature: str, timestamp: str, nonce: str) -> bool:
    items = sorted([settings.wechat_token, timestamp, nonce])
    digest = hashlib.sha1("".join(items).encode("utf-8")).hexdigest()
    return digest == signature


@router.get("/wechat")
def verify_wechat(signature: str, timestamp: str, nonce: str, echostr: str):
    if not _verify_signature(signature, timestamp, nonce):
        return Response("invalid signature", status_code=403)
    return Response(content=echostr, media_type="text/plain")


@router.post("/wechat")
async def receive_message(request: Request):
    raw = await request.body()
    if not raw:
        return Response("success", media_type="text/plain")

    root = ET.fromstring(raw.decode("utf-8"))
    msg_type = root.findtext("MsgType", default="")
    from_user = root.findtext("FromUserName", default="")
    to_user = root.findtext("ToUserName", default="")
    content = root.findtext("Content", default="").strip()

    if msg_type != "text":
        return Response(content=text_reply(from_user, to_user, "暂仅支持文本消息。"), media_type="application/xml")

    if settings.wechat_score_keyword in content:
        guide = f"请点击进入成绩查询页面：{settings.score_page_url}"
        return Response(content=text_reply(from_user, to_user, guide), media_type="application/xml")

    answer = qa_service.answer(content) if content else "暂无法解答"
    return Response(content=text_reply(from_user, to_user, answer), media_type="application/xml")
