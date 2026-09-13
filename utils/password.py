from passlib.context import CryptContext
from sqlalchemy.util import deprecated

# 创建密码处理器
pwd_context = CryptContext(
    # 算法使用bcrypt算法
    schemes=["bcrypt"],
    deprecated="auto"
)

# 密码加密
def hash_password(password:str):
    return pwd_context.hash(password)

# 密码验证
def verify_password(
        plain_password,
        hashed_password
):
    return pwd_context.verify(
        plain_password,
        hashed_password
    )