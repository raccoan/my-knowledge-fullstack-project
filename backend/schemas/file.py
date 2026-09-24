from datetime import datetime

from pydantic import BaseModel


class FileResponse(BaseModel):
    id: int
    filename: str
    file_path: str
    created_time: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.strftime("%Y-%m-%d %H:%M:%S")
        }


class KnowledgeFileResponse(BaseModel):
    id: int
    file_id: int
    filename: str
    status: str
    chunk_count: int
    file_size: int | None
    created_at: datetime