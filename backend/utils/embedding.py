import os

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

api_key = os.getenv("API_KEY")
base_url = os.getenv("BASE_URL")


api_key = os.getenv("API_KEY")
if not api_key:
    raise RuntimeError("API_KEY 未配置，请检查 backend/.env")


client = OpenAI(
    api_key = api_key,
    base_url = base_url
)


def get_embedding(text: str):
    # 【新增】在本地校验，避免把“缺少 prompt”的不透明错误交给供应商返回。
    normalized_text = text.strip() if isinstance(text, str) else ""
    if not normalized_text:
        raise ValueError("生成向量的文本不能为空")

    response = client.embeddings.create(
        model="embedding-3",
        input=normalized_text
    )

    return response.data[0].embedding