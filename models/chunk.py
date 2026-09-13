from sqlalchemy import  Column,Integer,Text
from database import Base

class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(
        Integer,
        primary_key=True
    )

    document_id = Column(
        Integer
    )

    content = Column(
        Text
    )
