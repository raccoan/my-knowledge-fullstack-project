from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    username = Column(
        String(50),
        nullable=False,
        unique=True,
        index=True
    )

    email = Column(
        String(255),
        nullable=True,
        unique=True,
        index=True
    )

    phone = Column(
        String(20),
        nullable=True,
        unique=True,
        index=True
    )

    password = Column(
        String(255),
        nullable=False
    )

    age = Column(
        Integer,
        nullable=True
    )

    created_at = Column(
        DateTime,
        server_default=func.now()
    )