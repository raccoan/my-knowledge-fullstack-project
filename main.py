from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import users
from routers import files
from routers import chat

app = FastAPI()

# CORS 跨域配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(files.router)
app.include_router(chat.router)