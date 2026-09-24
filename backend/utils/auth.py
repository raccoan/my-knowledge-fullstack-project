from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError

from utils.jwt import ALGORITHM, SECRET_KEY


oauth2_schema = OAuth2PasswordBearer(
    tokenUrl="/login"
)


def get_current_user(
    token: str = Depends(oauth2_schema)
):
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("user_id")

        if user_id is None:
            raise HTTPException(
                status_code=401,
                detail="token无效"
            )

        return {
            "id": user_id
        }

    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="token无效"
        )