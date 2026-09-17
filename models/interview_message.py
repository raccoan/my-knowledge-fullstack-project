from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func

from database import Base


class InterviewMessage(Base):
    __tablename__ = "interview_messages"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    interview_id = Column(
        Integer,
        nullable=False,
        index=True
    )

    role = Column(
        String(20),
        nullable=False
    )

    content = Column(
        Text,
        nullable=False
    )

    score = Column(
        Integer,
        nullable=True
    )

    feedback = Column(
        Text,
        nullable=True
    )

    created_at = Column(
        DateTime,
        server_default=func.now()
    )

    reference_answer = Column(
        Text,
        nullable=True,
    )