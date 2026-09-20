from sqlalchemy import Column, Integer, Text, DateTime, String
from database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        nullable=False,
        index=True
    )

    file_id = Column(
        Integer,
        nullable=True,
        index=True
    )

    content = Column(
        Text,
        nullable=True
    )

    created_time = Column(
        DateTime,
        nullable=False
    )

    status = Column(
        String(20),
        nullable=False,
        default="processing"
    )

    chunk_count = Column(
        Integer,
        nullable=False,
        default=0
    )