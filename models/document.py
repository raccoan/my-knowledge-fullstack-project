from sqlalchemy import Column,Integer,String,Text,DateTime
from datetime import  datetime
from database import Base

class Document(Base):
    __tablename__ = "document"

    id = Column(
        Integer,
        primary_key=True
    )

    file_id = Column(
        Integer
    )

    content = Column(
      Text
    )

    created_time = Column(
        DateTime,
        default=datetime.now
    )