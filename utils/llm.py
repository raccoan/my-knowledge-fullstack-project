import os
from dotenv import  load_dotenv
from openai import  OpenAI

load_dotenv()
client = OpenAI(
    api_key=os.getenv("API_KEY"),
    base_url="https://open.bigmodel.cn/api/paas/v4"
)

def chat_with_llm(question:str):
    response = client.chat.completions.create(
        model="glm-4.5",
        messages=[
            {
                "role":"user",
                "content":question
            }
        ],

    )
    return response.choices[0].message.content


def chat_with_llm_stream(question:str):
    print("开始调用LLM")
    response = client.chat.completions.create(
        model="glm-4.5",
        messages=[
            {
                "role":"user",
                "content":question
            }
        ],
        stream=True
    )

    print("LLM已经返回response")
    for chunk in response:
        print("收到chunk:",chunk)
        content=chunk.choices[0].delta.content
        if content:
            print("输出内容:",content)
            yield content
    print("LLM输出结束")

