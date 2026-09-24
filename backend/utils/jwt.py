# 第三方库 jose 提供生成 encode、解码验证 decode 的方法
from jose import jwt

# python 内置时间处理模块
from datetime import timedelta, datetime

from dotenv import load_dotenv
import os


# 加载 .env
load_dotenv()


# 密钥
SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY 未配置，请检查 backend/.env")


# 解密算法
ALGORITHM = "HS256"


# 创建 token
def create_token(data: dict):
    to_encode = data.copy()

    expire = datetime.now() + timedelta(minutes=30)

    to_encode.update({
        "exp": expire
    })

    token = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return token