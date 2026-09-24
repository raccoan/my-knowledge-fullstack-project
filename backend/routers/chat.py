
from fastapi.params import Depends
from sqlalchemy.orm import  Session

from database import get_db
from models.conversation import Conversation
from models.message import Message
from schemas.chat import ChatRequest
from utils.rag import rag_answer, build_prompt,retrieve_documents
from utils.llm import chat_with_llm_stream,generate_conversation_title
from fastapi import APIRouter,HTTPException
from fastapi.responses import StreamingResponse
from models.user import  User
from utils.auth import get_current_user
from sqlalchemy.sql import  func

import json


router = APIRouter()

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
        if conversation.title != "新对话":
            yield (
                    "data: "
                    + json.dumps(
                {
                    "type": "title",
                    "title": conversation.title
                },
                ensure_ascii=False
            )
                    + "\n\n"
            )

        yield (
                "data: "
                + json.dumps(
            {
                "type": "done"
            },
            ensure_ascii=False
        )
                + "\n\n"
        )

        yield (
            "data: "
            + json.dumps(
                {
                    "type": "done"
                },
                ensure_ascii=False
            )
            + "\n\n"
        )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )




