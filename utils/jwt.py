# 第三方库jose 提供生成encode 解码验证decode的方法
from jose import jwt
# python内置时间处理模块 datetime:处理具体时间点
# timedelta:处理时间间隔
from datetime import timedelta, datetime

# 密钥
SECRET_KEY = "my-secret-key"
# 解密算法 对称加密
ALGORITHM = "HS256"
# 创建token
def create_token(data:dict):
    to_encode = data.copy()
    expire = datetime.now() + timedelta(minutes=30)
    to_encode.update({
        "exp":expire
    })
    token = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return token


