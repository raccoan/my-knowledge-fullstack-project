from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from utils.verification import create_verification_code


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
    except ValueError as e:
        raise HTTPException(
            status_code=429,
            detail=str(e)
        )

    # 目前先打印验证码
    # 后续这里替换成真正的邮箱/短信发送
    print(
        f"[验证码] type={code_type}, "
        f"target={target}, "
        f"code={code}"
    )

    return {
        "message": "验证码发送成功"
    }