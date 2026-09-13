from aiohttp.web_response import StreamResponse
from fastapi.params import Depends

from schemas.chat import ChatRequest
from utils.rag import rag_answer, rag_answer_stream
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from models.user import  User
from utils.auth import get_current_user

router = APIRouter()

@router.post('/chat')
def chat(request:ChatRequest,current_user:User=Depends(get_current_user)):
    result = rag_answer(request.question,current_user["id"])
    return result

@router.post('/chat/stream')
def chat_stream(
        request:ChatRequest,
        current_user:User=Depends(get_current_user)
):
    def event_generator():
        for content in rag_answer_stream(
            request.question,
            current_user["id"]
        ):
            for line in content.splitlines():
                yield f"data:{line}\n"
            yield "\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-control":"no-chche",
            "Connection":"keep-alive"
        }
    )