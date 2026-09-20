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



def generate_interview_question(
    resume_data,
    weak_points=None,
    question_type="项目深挖",
    previous_questions=None
):
    weak_points = weak_points or []
    previous_questions = previous_questions or []

    # 历史薄弱知识点
    if weak_points:
        weak_point_context = "\n".join(
            f"- {item}"
            for item in weak_points
        )
    else:
        weak_point_context = "暂无历史薄弱知识点"

    # 已经问过的问题
    if previous_questions:
        previous_question_context = "\n".join(
            f"- {item}"
            for item in previous_questions
        )
    else:
        previous_question_context = "暂无"

    # 不同题型的强约束
    question_type_instruction = {
        "项目深挖": """
本题必须是项目深挖题。

重点考察：
- 项目具体实现
- 技术选型
- 架构设计
- 开发过程中遇到的问题
- 如何解决问题
- 为什么这样设计

不要直接考察纯八股。
不要重复已经问过的问题。
""",

        "技术原理": """
本题必须是技术原理/八股题。

必须考察候选人简历中出现的某项技术背后的原理。

例如：
- Vue3 响应式原理
- React Hooks 原理
- JavaScript 事件循环
- TypeScript 类型系统
- Fetch / SSE / HTTP
- FastAPI 依赖注入
- MySQL 索引
- RAG 检索原理

重点是“为什么”和“底层怎么工作”。

不要让问题只是简单询问项目实现。
""",

        "项目结合技术原理": """
本题必须同时结合“候选人的真实项目”和“技术原理”。

问题应该形成：

项目经历
+
项目中的具体技术
+
该技术背后的原理

例如：

“你在 AI 对话平台中使用了 SSE 实现流式输出，请解释 SSE 的工作机制，以及为什么这里适合使用 SSE？”

不能只问项目，也不能只问八股。
""",

        "实际场景": """
本题必须是实际开发场景题。

给候选人一个真实的软件开发问题，
让候选人分析原因并提出解决方案。

例如：
- 接口响应缓慢怎么办？
- 大文件上传怎么办？
- SSE连接断开怎么办？
- RAG检索结果不准确怎么办？
- 前端出现内存泄漏怎么办？
- 数据库查询越来越慢怎么办？

重点考察：
问题分析能力
+
技术方案设计能力

不要直接问定义类八股。
""",

        "薄弱知识点强化": """
本题必须针对候选人历史面试中出现的薄弱知识点。

必须从“历史薄弱知识点”中选择一个进行考察。

优先选择：
- 出现次数较多的知识点
- 与候选人简历技术栈相关的知识点

问题应该比之前的问题更加深入。

不能继续随机询问其他项目知识。

如果历史薄弱知识点为空，
则选择候选人简历中最核心的技术原理进行考察。
"""
    }

    instruction = question_type_instruction.get(
        question_type,
        question_type_instruction["项目深挖"]
    )

    prompt = f"""
你是一名专业的技术面试官。

现在正在进行一场真实的技术面试。

请根据候选人的真实简历生成下一道面试问题。

━━━━━━━━━━━━━━━━━━
【候选人简历】
━━━━━━━━━━━━━━━━━━

{json.dumps(
    resume_data,
    ensure_ascii=False,
    indent=2
)}

━━━━━━━━━━━━━━━━━━
【历史薄弱知识点】
━━━━━━━━━━━━━━━━━━

{weak_point_context}

━━━━━━━━━━━━━━━━━━
【已经问过的问题】
━━━━━━━━━━━━━━━━━━

{previous_question_context}

━━━━━━━━━━━━━━━━━━
【当前题型】
━━━━━━━━━━━━━━━━━━

{question_type}

━━━━━━━━━━━━━━━━━━
【本题必须遵守的题型要求】
━━━━━━━━━━━━━━━━━━

{instruction}

━━━━━━━━━━━━━━━━━━
【通用要求】
━━━━━━━━━━━━━━━━━━

1. 必须基于候选人的真实简历。
2. 不允许编造候选人没有经历过的项目。
3. 不允许编造候选人没有使用过的技术。
4. 必须严格遵守当前题型。
5. 不能与已经问过的问题重复。
6. 即使技术相同，也必须更换考察角度。
7. 问题应该符合真实技术面试场景。
8. 问题应该具有一定深度。
9. 不要一次提出很多完全无关的问题。
10. 只生成一道面试问题。
11. 不要返回答案。
12. 不要返回 JSON。
13. 不要使用 Markdown。
14. 不要添加“问题：”等前缀。

请直接输出面试问题。
"""

    response = client.chat.completions.create(
        model="glm-4.5",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.8
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
    "reference_answer": "",
    "knowledge_gap": [],
    "next_question": "",
    "finished": false
}}

评价要求：

1. score 为 0-100 的整数。

2. feedback 分析候选人的回答正确的地方和不足。

3. reference_answer：
   给出这道题一个适合技术面试场景的参考答案。
   不管候选人回答正确与否，都必须提供参考答案。

4. knowledge_gap：
   根据候选人的回答，列出候选人没有掌握或者回答不充分的知识点。

5. 必须区分：
   - 简历中写过但回答不清楚
   - 知识库中有相关内容但候选人没有掌握
   - 简历和知识库都没有足够信息

6. 不要因为简历写了某项技术，就默认候选人真的掌握。

7. 不要编造简历和知识库中不存在的候选人经历。

8. next_question 必须根据候选人的简历、当前问题和回答情况继续追问。
   优先围绕候选人的项目经历、技术栈和实际工作内容进行提问。

9. finished 表示模型认为当前面试是否适合结束。
   但是最终是否结束由后端控制。

10. 只返回 JSON。

11. 不要返回 Markdown。

12. 不要返回 ```json 或 ``` 包裹。
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




