
from sqlalchemy import Column,Integer,String,DateTime
from database import Base
from datetime import  datetime

class File(Base):
    __tablename__ = "files"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    filename = Column(
        String(255)
    )

    file_path = Column(
        String(255)
    )

    file_size = Column(Integer, nullable=True)

    user_id = Column(
        Integer
    )

    created_time = Column(
        DateTime,
        default=datetime.now
    )