# 数据库表模型
from sqlalchemy import Column,Integer,String
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    username = Column(
        String(50),
    )

    age = Column(
        Integer,
    )

    password = Column(
        String(255),
    )

