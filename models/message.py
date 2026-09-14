from sqlalchemy import Column,String,Integer,DateTime,Text
from sqlalchemy.sql import func

from database import  Base

class Message(Base):
    __tablename__ = "messages"

    id=Column(
        Integer,
        primary_key=True,
        index=True,
    )

    conversation_id=Column(
        Integer,
        nullable=False,
        index=True,
    )

    role = Column(
        String(20),
        nullable=False,
    )

    content = Column(
        Text,
        nullable=False,
    )

    created_at = Column(
        DateTime,
        server_default=func.now(),
    )