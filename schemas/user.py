# 请求数据模型
from pydantic import BaseModel, Field


class User(BaseModel):
    username: str
    password: str
    age: int | None = None


class RegisterRequest(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=50
    )

    email: str | None = None

    phone: str | None = None

    code: str = Field(
        min_length=6,
        max_length=6
    )

    password: str = Field(
        min_length=6,
        max_length=100
    )

    code_type:str


class LoginRequest(BaseModel):
    username: str
    password: str
