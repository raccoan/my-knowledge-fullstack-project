from fastapi import  Depends,HTTPException
from fastapi.security import OAuth2AuthorizationCodeBearer, OAuth2PasswordBearer

from jose import  jwt

from utils.jwt import ALGORITHM,SECRET_KEY

oauth2_schema = OAuth2PasswordBearer(
    tokenUrl="/login"
)
def get_current_user(
        token:str = Depends(oauth2_schema)
):
    try:
        payload = jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
        return payload
    except:
        raise HTTPException(
            status_code = 401,
            detail = "token无效"
        )