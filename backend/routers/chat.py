
from fastapi.params import Depends
from sqlalchemy.orm import  Session

from database import get_db,SessionLocal

from models.conversation import Conversation
from models.message import Message
from schemas.chat import ChatRequest
from utils.rag import rag_answer, build_prompt,retrieve_documents
from utils.llm import chat_with_llm_stream,generate_conversation_title
from fastapi import APIRouter,HTTPException,BackgroundTasks
from fastapi.responses import StreamingResponse
from models.user import  User
from utils.auth import get_current_user
from sqlalchemy.sql import  func

import json


router = APIRouter()

def generate_title_in_background(
    conversation_id: int,
    question: str,
    answer: str,
) -> None:
    """流式回答完成后再生成标题，标题慢不会阻塞 SSE 的 done 事件。"""
    db = SessionLocal()
    try:
        conversation = (
            db.query(Conversation)
            .filter(Conversation.id == conversation_id)
            .first()
        )

        # 用户已经手动改名时，不覆盖其标题。
        if not conversation or conversation.title != "新对话":
            return

        title = generate_conversation_title(question, answer).strip()
        if title:
            conversation.title = title[:50]
            conversation.updated_at = func.now()
            db.commit()
    except Exception as error:
        db.rollback()
        print(f"会话 {conversation_id} 自动生成标题失败：{error}")
    finally:
        db.close()

@router.post('/chat')
def chat(request:ChatRequest,current_user:User=Depends(get_current_user)):
    result = rag_answer(request.question,current_user["id"])
    return result


@router.post("/chat/stream")
def chat_stream(
    request: ChatRequest,
    background_tasks:BackgroundTasks,
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

        answer_parts = []

        for content in chat_with_llm_stream(
            prompt
        ):
            answer_parts.append(content)

            yield (
                "data: "
                + json.dumps(
                    {
                        "type": "content",
                        "content": content
                    },
                    ensure_ascii=False
                )
                + "\n\n"
            )

        answer = "".join(answer_parts)

        assistant_message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=answer
        )

        db.add(assistant_message)

        # 自动生成会话标题
        if conversation.title == "新对话":
            new_title = generate_conversation_title(
                request.question,
                answer,
            )

            conversation.title = new_title

        conversation.updated_at = func.now()

        db.commit()

        # 如果生成了新标题，通知前端
        # 【优化】标题改为后台任务；回答完成不再等待第二次 LLM 调用。
        if conversation.title == "新对话":
            background_tasks.add_task(
                generate_title_in_background,
                conversation.id,
                request.question,
                answer,
            )

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
        background=background_tasks,
    )




