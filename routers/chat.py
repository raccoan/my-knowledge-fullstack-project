from aiohttp.web_response import StreamResponse
from fastapi.params import Depends

from schemas.chat import ChatRequest
from utils.rag import rag_answer, build_prompt,retrieve_documents
from utils.llm import chat_with_llm_stream
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from models.user import  User
from utils.auth import get_current_user

import json


router = APIRouter()

@router.post('/chat')
def chat(request:ChatRequest,current_user:User=Depends(get_current_user)):
    result = rag_answer(request.question,current_user["id"])
    return result

@router.post("/chat/stream")
def chat_stream(
    request: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    user_id = current_user["id"]

    sources = retrieve_documents(
        request.question,
        user_id
    )

    prompt = build_prompt(
        request.question,
        sources
    )

    def event_generator():

        # 1. 先发送来源
        yield (
            "data: "
            + json.dumps(
                {
                    "type": "sources",
                    "sources": sources,
                },
                ensure_ascii=False
            )
            + "\n\n"
        )

        # 2. 再流式发送 AI 内容
        for content in chat_with_llm_stream(prompt):

            yield (
                "data: "
                + json.dumps(
                    {
                        "type": "content",
                        "content": content,
                    },
                    ensure_ascii=False
                )
                + "\n\n"
            )

        # 3. 结束
        yield (
            "data: "
            + json.dumps(
                {
                    "type": "done"
                }
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