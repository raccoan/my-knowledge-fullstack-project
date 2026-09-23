# 验证码生成工具
import random
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from models.verification_code import VerificationCode


def generate_code():
    """
    生成6位数字验证码
    """
    return str(random.randint(100000, 999999))


def create_verification_code(
    db: Session,
    target: str,
    code_type: str
):
    """
    创建验证码
    """

    # 查询最近发送的验证码
    latest_code = (
        db.query(VerificationCode)
        .filter(
            VerificationCode.target == target,
            VerificationCode.type == code_type
        )
        .order_by(
            VerificationCode.created_at.desc()
        )
        .first()
    )

    # 60秒内不能重复发送
    if latest_code:
        if (
            latest_code.created_at
            and
            (
                datetime.now()
                - latest_code.created_at
            ).total_seconds() < 60
        ):
            raise ValueError(
                "验证码发送过于频繁，请稍后再试"
            )

    code = generate_code()

    expires_at = (
        datetime.now()
        + timedelta(minutes=5)
    )

    verification_code = VerificationCode(
        target=target,
        code=code,
        type=code_type,
        expires_at=expires_at
    )

    db.add(verification_code)
    db.commit()

    return code


def verify_code(
    db: Session,
    target: str,
    code: str,
    code_type: str
):
    """
    验证验证码
    """

    verification_code = (
        db.query(VerificationCode)
        .filter(
            VerificationCode.target == target,
            VerificationCode.code == code,
            VerificationCode.type == code_type
        )
        .order_by(
            VerificationCode.created_at.desc()
        )
        .first()
    )

    if not verification_code:
        return False

    if (
        verification_code.expires_at
        < datetime.now()
    ):
        return False

    # 验证成功后删除验证码
    db.delete(verification_code)
    db.commit()

    return True