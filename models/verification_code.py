from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func

from database import Base


class VerificationCode(Base):
    __tablename__ = "verification_codes"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    target = Column(
        String(255),
        nullable=False,
        index=True
    )

    code = Column(
        String(10),
        nullable=False
    )

    type = Column(
        String(20),
        nullable=False
    )

    expires_at = Column(
        DateTime,
        nullable=False
    )

    created_at = Column(
        DateTime,
        server_default=func.now()
    )