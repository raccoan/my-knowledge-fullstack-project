# 数据库连接
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

DATABASE_URL = "mysql+pymysql://root:041215@localhost:3306/fastapi_demo"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)
Base = declarative_base()

# 获取数据库连接
from sqlalchemy import text


def get_db():
    db = SessionLocal()

    try:
        result = db.execute(text("SELECT DATABASE()"))
        print("当前连接数据库:", result.fetchone())

        yield db

    finally:
        db.close()