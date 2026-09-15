import os
from dotenv import  load_dotenv
from openai import  OpenAI
import json

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

def parse_resume_with_llm(resume_text: str):
    prompt = f"""
你是一名专业的招聘系统简历解析器。

请分析下面的简历内容，并严格按照指定 JSON 格式返回。

要求：
1. 只能根据简历内容提取信息
2. 不要编造不存在的信息
3. 找不到的信息使用空字符串、空数组或空对象
4. 只返回 JSON
5. 不要返回 Markdown
6. 不要返回 ```json
7. 保留项目经历中的技术细节
8. 保留实习经历中的工作内容
9. 技能按照简历原文进行归类

JSON 格式：

{{
    "basic_info": {{
        "name": "",
        "phone": "",
        "email": "",
        "location": ""
    }},
    "education": [
        {{
            "school": "",
            "major": "",
            "degree": "",
            "start_date": "",
            "end_date": ""
        }}
    ],
    "skills": [],
    "projects": [
        {{
            "name": "",
            "description": "",
            "technologies": [],
            "responsibilities": [],
            "highlights": []
        }}
    ],
    "internships": [
        {{
            "company": "",
            "position": "",
            "start_date": "",
            "end_date": "",
            "responsibilities": [],
            "technologies": []
        }}
    ],
    "self_evaluation": ""
}}

简历内容：

----------------
{resume_text}
----------------
"""

    response = client.chat.completions.create(
        model="glm-4.5",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0
    )

    content = response.choices[0].message.content

    # 防止模型偶尔返回 ```json
    content = content.strip()

    if content.startswith("```"):
        content = content.replace("```json", "")
        content = content.replace("```", "")
        content = content.strip()

    return json.loads(content)
