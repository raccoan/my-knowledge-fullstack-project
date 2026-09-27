
from fastapi.params import Depends
from sqlalchemy.orm import  Session

from database import get_db

from models.conversation import Conversation
from models.message import Message
from schemas.chat import ChatRequest
from utils.rag import rag_answer, build_prompt,retrieve_documents
from utils.llm import chat_with_llm_stream
from fastapi import APIRouter,HTTPException
from fastapi.responses import StreamingResponse
from models.user import  User
from utils.auth import get_current_user
from sqlalchemy.sql import  func

import json


router = APIRouter()

def create_title_from_question(question: str, max_length: int = 22) -> str:
    """【新增】根据用户问题立即生成稳定的临时标题，不等待 LLM。"""
    normalized = " ".join((question or "").split())
    if not normalized:
        return "新对话"

    # 去除常见礼貌前缀，让标题直接呈现主题关键词。
    for prefix in ("请问", "请", "帮我", "麻烦", "你好，", "你好"):
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix):].lstrip(" ，,：:")
            break

    if len(normalized) > max_length:
        return normalized[:max_length] + "…"
    return normalized

@router.post('/chat')
def chat(request:ChatRequest,current_user:User=Depends(get_current_user)):
    result = rag_answer(request.question,current_user["id"])
    return result


@router.post("/chat/stream")
def chat_stream(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    )
):
    user_id = current_user["id"]

    conversation = (
        db.query(Conversation)
        .filter(
            Conversation.id ==
            request.conversation_id,
            Conversation.user_id ==
            user_id
        )
        .first()
    )

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="会话不存在"
        )

    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=request.question
    )

    db.add(user_message)

    # 【新增】用户发送问题后马上更新标题；不再依赖回答完成后的第二次 LLM 调用。
    title_changed = False
    if conversation.title == "新对话":
        conversation.title = create_title_from_question(request.question)
        title_changed = True

    conversation.updated_at = func.now()
    db.commit()

    sources = retrieve_documents(
        request.question,
        user_id,
        db
    )

    prompt = build_prompt(
        request.question,
        sources
    )

    def event_generator():
        answer_parts = []
        completed = False

        try:
            # 【新增】将即时标题通知给前端，侧栏无需等待刷新或回答结束。
            if title_changed:
                yield (
                    "data: "
                    + json.dumps(
                        {"type": "title", "title": conversation.title},
                        ensure_ascii=False,
                    )
                    + "\n\n"
                )

            yield (
                "data: "
                + json.dumps(
                    {
                        "type": "sources",
                        "sources": sources
                    },
                    ensure_ascii=False
                )
                + "\n\n"
            )

            for content in chat_with_llm_stream(prompt):
                answer_parts.append(content)
                yield (
                    "data: "
                    + json.dumps(
                        {"type": "content", "content": content},
                        ensure_ascii=False,
                    )
                    + "\n\n"
                )

            completed = True
        finally:
            # 【新增】无论正常完成、用户停止还是断开页面，都保存本轮可用内容。
            answer = "".join(answer_parts).strip()
            if not answer:
                answer = "本次回答已停止，可点击“重新生成”再次尝试。"

            db.add(Message(
                conversation_id=conversation.id,
                role="assistant",
                content=answer,
            ))
            conversation.updated_at = func.now()
            db.commit()

        if completed:
            yield (
                "data: "
                + json.dumps({"type": "done"}, ensure_ascii=False)
                + "\n\n"
            )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )




