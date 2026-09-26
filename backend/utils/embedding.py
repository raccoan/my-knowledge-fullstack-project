import os

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

api_key = os.getenv("API_KEY")
base_url = os.getenv("BASE_URL")

client = OpenAI(
    api_key = api_key,
    base_url = base_url
)


def get_embedding(text: str):

    response = client.embeddings.create(
        model="embedding-3",
        input=text
    )

    return response.data[0].embedding