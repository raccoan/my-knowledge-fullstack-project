from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy.orm import Session
from database import get_db
from models.conversation import Conversation
from models.message import Message

from utils.auth import get_current_user

router = APIRouter()

# 创建新对话接口
@router.post("/conversations")
def create_conversation(
        db:Session=Depends(get_db),
        current_user = Depends(get_current_user),
):
    user_id=current_user["id"]
    conversation = Conversation(
        user_id=user_id,
        title="新对话"
    )

    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return {
        "user_id":user_id,
        "title":conversation.title,
        "created_at":conversation.created_at,
        "updated_at":conversation.updated_at,
    }

# 获取当前用户所有对话接口
@router.get("/conversations")
def get_conversations(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    user_id = current_user["id"]

    conversations = (
        db.query(Conversation)
        .filter(Conversation.user_id == user_id)
        .order_by(Conversation.updated_at.desc())
        .all()
    )

    return [
        {
            "id": item.id,
            "title": item.title,
            "created_at": item.created_at,
            "updated_at": item.updated_at,
        }
        for item in conversations
    ]

# 获取单个会话接口
@router.get("/conversations/{conversation_id}")
def get_conversation(
        conversation_id: int,
        db:Session=Depends(get_db),
        current_user=Depends(get_current_user),
):
    user_id=current_user["id"]
    conversation = db.query(Conversation).filter(
        Conversation.id==conversation_id,
        Conversation.user_id==user_id
    ).first()

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="会话不存在",
        )
    return conversation

# 获取某单独会话下的所有消息接口
@router.get("/conversations/{conversation_id}/messages")
def get_messages(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    user_id = current_user["id"]

    conversation = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id
        )
        .first()
    )

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="会话不存在"
        )

    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .all()
    )

    return [
        {
            "id": item.id,
            "conversation_id": item.conversation_id,
            "role": item.role,
            "content": item.content,
            "created_at": item.created_at,
        }
        for item in messages
    ]

# 删除某个会话接口
@router.delete("/conversations/{conversation_id}")
def delete_conversation(
        conversation_id:int,
        db:Session=Depends(get_db),
        current_user = Depends(get_current_user),
):
    user_id=current_user["id"]
    conversation = (db.query(Conversation).filter(
        Conversation.id==conversation_id,
        Conversation.user_id==user_id,
        ).first()
    )
    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="会话不存在",

        )

#     删除会话下的消息 避免消息依赖会话而出错
    db.query(Message).filter(
        Message.conversation_id==conversation_id,
    ).delete(
        synchronize_session=False
    )

    db.delete(conversation)
    db.commit()
    return{
        "message":"删除成功"
    }

