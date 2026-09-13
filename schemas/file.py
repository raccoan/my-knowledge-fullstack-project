from pydantic import BaseModel
from datetime import  datetime

class FileResponse(BaseModel):
    id:int
    filename:str
    file_path:str
    created_time:datetime

    class Config:
        from_attributes = True
        # 修改返回时间的格式
        json_encoders = {
            datetime: lambda v: v.strftime("%Y-%m-%d %H:%M:%S")
        }