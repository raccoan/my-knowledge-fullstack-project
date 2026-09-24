from datetime import datetime

from pydantic import BaseModel


class ChunkResponse(BaseModel):
    id: int
    chunk_index: int
    content: str


class DocumentDetailResponse(BaseModel):
    id: int
    file_id: int
    filename: str
    file_size: int | None
    status: str
    chunk_count: int
    created_at: datetime
    chunks: list[ChunkResponse]