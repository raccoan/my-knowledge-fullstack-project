from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from sqlalchemy.orm import Session

from database import get_db
from utils.verification import (
    create_verification_code
)
from utils.notification import (
    send_email_code,
    send_phone_code
)


router = APIRouter()


@router.post("/send-code")
def send_code(
    target: str,
    code_type: str,
    db: Session = Depends(get_db)
):
    if code_type not in ["email", "phone"]:
        raise HTTPException(
            status_code=400,
            detail="验证码类型错误"
        )

    if not target:
        raise HTTPException(
            status_code=400,
            detail="邮箱或手机号不能为空"
        )

    try:
        code = create_verification_code(
            db,
            target,
            code_type
        )

        if code_type == "email":
            send_email_code(
                target,
                code
            )

        else:
            send_phone_code(
                target,
                code
            )

    except ValueError as e:
        raise HTTPException(
            status_code=429,
            detail=str(e)
        )

    except ValueError as e:
        raise HTTPException(
            status_code=429,
            detail=str(e)
        )

    except Exception as e:
        print(
            f"验证码发送失败：{e}"
        )

        raise HTTPException(
            status_code=500,
            detail="验证码发送失败，请稍后重试"
        )

    return {
        "message": "验证码发送成功"
    }