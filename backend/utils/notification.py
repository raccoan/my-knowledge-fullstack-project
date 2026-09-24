import json
import os
import smtplib

from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr

from dotenv import load_dotenv

load_dotenv()


# =========================
# 邮箱
# =========================

def send_email_code(
    email: str,
    code: str
):
    """
    通过 SMTP 发送邮箱验证码
    """

    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(
        os.getenv("SMTP_PORT", "465")
    )
    smtp_username = os.getenv(
        "SMTP_USERNAME"
    )
    smtp_password = os.getenv(
        "SMTP_PASSWORD"
    )

    if not all([
        smtp_host,
        smtp_username,
        smtp_password
    ]):
        raise RuntimeError(
            "SMTP配置不完整，请检查.env"
        )

    message = MIMEText(
        f"""
您好！

您的注册验证码是：

{code}

验证码有效期为5分钟。

如果不是您本人操作，请忽略此邮件。
""",
        "plain",
        "utf-8"
    )

    # 发件人
    message["From"] = formataddr(
        (
            str(Header(
                "知识库平台",
                "utf-8"
            )),
            smtp_username
        )
    )

    # 收件人
    message["To"] = email

    # 邮件标题
    message["Subject"] = str(
        Header(
            "知识库平台注册验证码",
            "utf-8"
        )
    )

    with smtplib.SMTP_SSL(
        smtp_host,
        smtp_port
    ) as server:

        server.login(
            smtp_username,
            smtp_password
        )

        server.sendmail(
            smtp_username,
            [email],
            message.as_string()
        )


# =========================
# todo:阿里云短信
# =========================

def send_phone_code(
    phone: str,
    code: str
):
    """
    通过阿里云短信发送验证码
    """

    from alibabacloud_dysmsapi20170525.client import (
        Client as Dysmsapi20170525Client
    )
    from alibabacloud_tea_openapi import (
        models as open_api_models
    )
    from alibabacloud_dysmsapi20170525 import (
        models as dysmsapi_20170525_models
    )
    from alibabacloud_tea_util import (
        models as util_models
    )

    access_key_id = os.getenv(
        "ALIBABA_CLOUD_ACCESS_KEY_ID"
    )

    access_key_secret = os.getenv(
        "ALIBABA_CLOUD_ACCESS_KEY_SECRET"
    )

    sign_name = os.getenv(
        "ALIYUN_SMS_SIGN_NAME"
    )

    template_code = os.getenv(
        "ALIYUN_SMS_TEMPLATE_CODE"
    )

    if not all([
        access_key_id,
        access_key_secret,
        sign_name,
        template_code
    ]):
        raise RuntimeError(
            "阿里云短信配置不完整，请检查.env"
        )

    config = open_api_models.Config(
        access_key_id=access_key_id,
        access_key_secret=access_key_secret
    )

    config.endpoint = "dysmsapi.aliyuncs.com"

    client = Dysmsapi20170525Client(
        config
    )

    request = dysmsapi_20170525_models.SendSmsRequest(
        phone_numbers=phone,
        sign_name=sign_name,
        template_code=template_code,
        template_param=json.dumps(
            {
                "code": code
            },
            ensure_ascii=False
        )
    )

    runtime = util_models.RuntimeOptions()

    client.send_sms_with_options(
        request,
        runtime
    )