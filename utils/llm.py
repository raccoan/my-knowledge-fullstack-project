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



def generate_interview_question(resume_data):
    prompt = f"""
你是一名专业的前端技术面试官。

现在你正在对候选人进行一场真实的技术面试。

候选人的结构化简历如下：

{json.dumps(resume_data, ensure_ascii=False, indent=2)}

请根据候选人的真实简历生成第一道面试题。

要求：

1. 必须结合候选人的真实项目经历
2. 优先询问项目中的技术实现细节
3. 不要问简历中完全没有出现的项目
4. 不要只问简单的八股题
5. 问题应该能够判断候选人是否真正做过这个项目
6. 如果有多个项目，优先选择技术含量最高的项目
7. 只返回面试问题本身
8. 不要添加“问题：”等前缀
"""

    response = client.chat.completions.create(
        model="glm-4.5",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.7
    )

    return response.choices[0].message.content.strip()


def evaluate_interview_answer(
    resume_data,
    question,
    answer
):
    prompt = f"""
你是一名专业的技术面试官。

请根据候选人的简历、面试问题和候选人的回答，对回答进行评价。

候选人简历：

{json.dumps(
    resume_data,
    ensure_ascii=False,
    indent=2
)}

面试问题：

{question}

候选人回答：

{answer}

请严格返回 JSON：

{{
    "score": 0,
    "feedback": "",
    "next_question": "",
    "finished": false
}}

评分规则：

90-100：
回答准确、完整，能够结合项目实际实现说明。

80-89：
回答基本正确，有一定项目实践，但细节不足。

70-79：
核心思路基本正确，但存在明显遗漏。

60-69：
只掌握部分基础知识，项目实践不足。

0-59：
回答错误、含糊或者明显不了解相关技术。

feedback：
说明回答做得好的地方以及具体不足。

next_question：
根据候选人的回答继续追问。

重点：
1. 追问必须结合候选人的简历
2. 如果回答暴露出知识薄弱点，可以针对该知识点继续追问
3. 不要突然跳到与简历无关的话题
4. 如果已经足够完成一轮面试，可以将 finished 设置为 true
5. 只返回 JSON
6. 不要返回 Markdown
7. 不要返回 ```json
"""

    response = client.chat.completions.create(
        model="glm-4.5",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.5
    )

    content = response.choices[0].message.content.strip()

    if content.startswith("```"):
        content = content.replace("```json", "")
        content = content.replace("```", "")
        content = content.strip()

    return json.loads(content)


def evaluate_interview_answer_with_knowledge(
    resume_data,
    knowledge_sources,
    question,
    answer
):
    knowledge_context = "\n\n".join(
        [
            source["content"]
            for source in knowledge_sources
        ]
    )

    prompt = f"""
你是一名专业的技术面试官。

请根据以下四部分信息评价候选人的回答：

【候选人简历】
{json.dumps(
    resume_data,
    ensure_ascii=False,
    indent=2
)}

【候选人的知识库内容】
{knowledge_context}

【面试问题】
{question}

【候选人回答】
{answer}

请返回严格 JSON：

{{
    "score": 0,
    "feedback": "",
    "knowledge_gap": [],
    "next_question": "",
    "finished": false
}}

评价要求：

1. score 为 0-100 的整数。
2. feedback 说明回答正确的地方和不足。
3. knowledge_gap 表示候选人回答暴露出的知识薄弱点。
4. 必须区分：
   - 简历中写过但回答不清楚
   - 知识库中有相关内容但候选人没有掌握
   - 简历和知识库都没有足够信息
5. 不要因为简历写了某项技术，就默认候选人真的掌握。
6. 不要编造知识库不存在的内容。
7. next_question 必须继续围绕简历中的项目或技术进行追问。
8. 如果已经完成本轮面试，将 finished 设置为 true。
9. 只返回 JSON。
10. 不要返回 Markdown。
"""

    response = client.chat.completions.create(
        model="glm-4.5",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.5
    )

    content = response.choices[0].message.content.strip()

    if content.startswith("```"):
        content = content.replace(
            "```json",
            ""
        )
        content = content.replace(
            "```",
            ""
        )
        content = content.strip()

    return json.loads(content)

def generate_interview_report(
    resume_data,
    interview_records,
    knowledge_sources
):
    prompt = f"""
你是一名专业的技术面试评估专家。

请根据候选人的简历、面试记录以及知识库内容生成最终面试报告。

【简历】
{json.dumps(
    resume_data,
    ensure_ascii=False,
    indent=2
)}

【面试记录】
{json.dumps(
    interview_records,
    ensure_ascii=False,
    indent=2
)}

【知识库相关内容】
{json.dumps(
    knowledge_sources,
    ensure_ascii=False,
    indent=2
)}

请严格返回：

{{
    "overall_score": 0,
    "project_ability": 0,
    "technical_ability": 0,
    "practical_ability": 0,
    "communication_ability": 0,
    "strengths": [],
    "weaknesses": [],
    "knowledge_gaps": [],
    "suggestions": []
}}

要求：

1. 所有分数为 0-100。
2. 不要因为简历写了某项技术就默认候选人掌握。
3. 根据实际回答判断项目能力。
4. 根据回答和知识库判断知识掌握情况。
5. knowledge_gaps 只填写实际暴露出的薄弱知识点。
6. 不要编造面试记录中没有出现的信息。
7. 只返回 JSON。
"""

    response = client.chat.completions.create(
        model="glm-4.5",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.3
    )

    content = response.choices[0].message.content.strip()

    if content.startswith("```"):
        content = content.replace(
            "```json",
            ""
        )
        content = content.replace(
            "```",
            ""
        )
        content = content.strip()

    return json.loads(content)




