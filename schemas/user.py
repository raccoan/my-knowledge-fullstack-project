# 请求数据模型

from pydantic import BaseModel

class User(BaseModel):
    username: str
    age: int
    password:str

class LoginRequest(BaseModel):
    username:str
    password:str
