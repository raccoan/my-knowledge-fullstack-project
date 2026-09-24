import os

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


client = OpenAI(
    api_key='da428c912681466e9b9d6e3f092680e3.HRIuqug8tolp4kta',
    base_url="https://open.bigmodel.cn/api/paas/v4"
)


def get_embedding(text: str):

    response = client.embeddings.create(
        model="embedding-3",
        input=text
    )

    return response.data[0].embedding