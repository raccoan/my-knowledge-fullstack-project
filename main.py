from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import users
from routers import files
from routers import chat
from routers import conversations
from routers import  resumes
from routers import  interviews
from routers import  verification

from models.user import User
from models.file import File
from models.document import Document
from models.chunk import Chunk
from models.conversation import Conversation
from models.message import Message
from models.resume import  Resume
from models.interview_message import  InterviewMessage
from models.interview import Interview

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

@app.get("/")
def root():
    return {
        "message": "FastAPI is running"
    }
app.include_router(users.router)
app.include_router(verification.router)
app.include_router(files.router)
app.include_router(chat.router)
app.include_router(conversations.router)
app.include_router(resumes.router)
app.include_router(interviews.router)