# 数据库连接
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv
import os

# 加载 .env
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL 未配置，请检查 backend/.env")

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


# 获取数据库连接
def get_db():
    db = SessionLocal()

    try:
        result = db.execute(text("SELECT DATABASE()"))
        print("当前连接数据库:", result.fetchone())

        yield db

    finally:
        db.close()