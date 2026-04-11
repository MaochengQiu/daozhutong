import hashlib
import xml.etree.ElementTree as ET

from fastapi import APIRouter, Request, Response

from app.config import get_settings
from app.qa import answer_question
from app.wechat.reply import text_reply


router = APIRouter()
settings = get_settings()


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

    try:
        root = ET.fromstring(raw.decode("utf-8"))
    except Exception:
        return Response("invalid xml", status_code=400)

    msg_type = root.findtext("MsgType", default="")
    from_user = root.findtext("FromUserName", default="")
    to_user = root.findtext("ToUserName", default="")
    content = root.findtext("Content", default="").strip()

    if msg_type != "text":
        return Response(
            content=text_reply(from_user, to_user, "目前仅支持处理文本消息。"),
            media_type="application/xml"
        )

    # 1. 关键词触发：查成绩
    if settings.wechat_score_keyword in content:
        guide = f"请点击进入成绩查询页面：{settings.score_page_url}"
        return Response(
            content=text_reply(from_user, to_user, guide),
            media_type="application/xml"
        )

    # 2. 知识库/AI 问答
    answer = await answer_question(content) if content else "你想问什么呢？"
    return Response(
        content=text_reply(from_user, to_user, answer),
        media_type="application/xml"
    )
