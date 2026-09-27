import os
from dotenv import  load_dotenv
from openai import  OpenAI
import json
from typing import  Any
from utils.structured_json import ResumeParseResult, request_validated_json, InterviewEvaluationResult
load_dotenv()
client = OpenAI(
    api_key=os.getenv("API_KEY"),
    base_url=os.getenv("BASE_URL")
)


def _ask_llm(
    prompt: str,
    *,
    temperature: float = 0,
    max_tokens: int = 800,
) -> str:
    """统一 LLM 请求入口，并限制生成长度，避免无意义的长输出。"""
    response = client.chat.completions.create(
        model="glm-4.5",
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content or ""


def _clip_text(value: Any, max_length: int) -> str:
    """截断上下文中的长文本，降低输入 token 数。"""
    text = str(value or "").strip()
    if len(text) <= max_length:
        return text
    return text[:max_length] + "…"


def _compact_resume_for_interview(resume_data: Any) -> dict[str, Any]:
    """只保留出题/评分需要的简历字段，避免每轮发送完整简历 JSON。"""
    if not isinstance(resume_data, dict):
        return {}

    projects = []
    for item in resume_data.get("projects", [])[:2]:
        if not isinstance(item, dict):
            continue
        projects.append({
            "name": _clip_text(item.get("name"), 80),
            "description": _clip_text(item.get("description"), 500),
            "technologies": item.get("technologies", [])[:12],
            "responsibilities": item.get("responsibilities", [])[:5],
            "highlights": item.get("highlights", [])[:5],
        })

    internships = []
    for item in resume_data.get("internships", [])[:1]:
        if not isinstance(item, dict):
            continue
        internships.append({
            "company": _clip_text(item.get("company"), 80),
            "position": _clip_text(item.get("position"), 80),
            "responsibilities": item.get("responsibilities", [])[:5],
            "technologies": item.get("technologies", [])[:12],
        })

    return {
        "skills": resume_data.get("skills", [])[:20],
        "projects": projects,
        "internships": internships,
    }




def generate_conversation_title(
    question,
    answer
):

    prompt = f"""
你是一个AI助手。

请根据下面的用户问题和AI回答，
生成一个简洁的会话标题。

要求：

1. 标题控制在15个字以内。
2. 不要带标点。
3. 不要出现“关于”“讨论”等无意义词。
4. 只返回标题文本。


用户问题：
{question}


AI回答：
{answer}

"""


    response = client.chat.completions.create(
        model="glm-4.5",
        messages=[
            {
                "role":"user",
                "content":prompt
            }
        ],
        temperature=0.5
    )


    title = (
        response
        .choices[0]
        .message
        .content
        .strip()
    )


    return title



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


    for chunk in response:

        content = (
            chunk
            .choices[0]
            .delta
            .content
        )

        if content:
            yield content

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
    #
    # response = client.chat.completions.create(
    #     model="glm-4.5",
    #     messages=[
    #         {
    #             "role": "user",
    #             "content": prompt
    #         }
    #     ],
    #     temperature=0
    # )
    #
    # content = response.choices[0].message.content
    #
    # # 防止模型偶尔返回 ```json
    # content = content.strip()
    #
    # if content.startswith("```"):
    #     content = content.replace("```json", "")
    #     content = content.replace("```", "")
    #     content = content.strip()
    #
    # return json.loads(content)
    return request_validated_json(
        request_fn=_ask_llm,
        prompt=prompt,
        schema=ResumeParseResult,
        max_attempts=2,
    )


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

    # 【新增】部分模型网关在异常或限流时可能返回空 content；不能把它当题目保存。
    content = response.choices[0].message.content or ""
    question = content.strip()
    if not question:
        raise RuntimeError("LLM 未返回有效面试问题")

    return question


def generate_interview_question(
    resume_data,
    weak_points=None,
    question_type="项目深挖",
    previous_questions=None
):
    """根据精简后的简历信息生成一题面试题。"""
    weak_points = weak_points or []
    previous_questions = previous_questions or []

    question_type_instruction = {
        "项目深挖": "围绕项目中的具体实现、技术选型或问题解决提问，不问纯定义。",
        "技术原理": "围绕简历出现的技术原理提问，重点问为什么与实现机制。",
        "项目结合技术原理": "问题必须同时包含真实项目场景与相关技术原理。",
        "实际场景": "给出与简历技术栈相关的真实开发场景，让候选人分析方案。",
        "薄弱知识点强化": "优先针对历史薄弱知识点；若为空则选择核心技术原理。",
    }

    compact_resume = _compact_resume_for_interview(resume_data)
    compact_weak_points = [
        _clip_text(item, 80)
        for item in weak_points[:5]
        if _clip_text(item, 80)
    ]
    compact_previous_questions = [
        _clip_text(item, 240)
        for item in previous_questions[-5:]
        if _clip_text(item, 240)
    ]

    prompt = f"""
你是技术面试官。只基于下面的候选人信息生成一道中文面试题。

候选人信息：
{json.dumps(compact_resume, ensure_ascii=False, separators=(",", ":"))}

历史薄弱点：{json.dumps(compact_weak_points, ensure_ascii=False)}
已问问题：{json.dumps(compact_previous_questions, ensure_ascii=False)}
题型：{question_type}
题型要求：{question_type_instruction.get(question_type, question_type_instruction["项目深挖"])}

要求：
1. 只能依据候选人信息，不得编造经历或技术。
2. 不重复已问问题。
3. 只输出一道问题，不输出答案、解释、Markdown 或“问题：”前缀。
""".strip()

    question = _ask_llm(
        prompt,
        temperature=0.4,
        max_tokens=180,
    ).strip()

    if not question:
        raise RuntimeError("LLM 未返回有效面试问题")

    return question



def evaluate_interview_answer_with_knowledge(
    resume_data,
    knowledge_sources,
    question,
    answer
):
    """评价回答并生成下一题；输入上下文和输出均受限，减少模型等待时间。"""
    compact_resume = _compact_resume_for_interview(resume_data)

    # 仅传递最相关的 3 个检索片段，每段最多 1200 个字符。
    compact_sources = [
        {
            "filename": _clip_text(source.get("filename"), 120),
            "content": _clip_text(source.get("content"), 1200),
        }
        for source in (knowledge_sources or [])[:3]
        if isinstance(source, dict) and source.get("content")
    ]

    prompt = f"""
你是技术面试官。请评价候选人的回答，并只返回 JSON。

候选人简历摘要：
{json.dumps(compact_resume, ensure_ascii=False, separators=(",", ":"))}

相关知识库片段：
{json.dumps(compact_sources, ensure_ascii=False, separators=(",", ":"))}

面试问题：{_clip_text(question, 500)}
候选人回答：{_clip_text(answer, 4000)}

JSON 格式：
{{
  "score": 0,
  "feedback": "",
  "reference_answer": "",
  "knowledge_gap": [],
  "next_question": "",
  "finished": false
}}

规则：
1. score 是 0 到 100 的整数。
2. feedback 不超过 100 字，只写优点和一个主要不足。
3. reference_answer 不超过 200 字，只写核心答题思路。
4. knowledge_gap 最多 3 项；不得把简历未出现的技术当成候选人经历。
5. next_question 只给一道与当前简历和回答相关的追问，最多 80 字。
6. 只返回 JSON，不要 Markdown 或解释。
""".strip()

    try:
        # 一次调用失败时返回现有兜底结果，不在用户等待时额外重试。
        return request_validated_json(
            request_fn=lambda current_prompt: _ask_llm(
                current_prompt,
                temperature=0.2,
                max_tokens=520,
            ),
            prompt=prompt,
            schema=InterviewEvaluationResult,
            max_attempts=1,
        )
    except (ValueError, json.JSONDecodeError):
        return {
            "score": 0,
            "feedback": "AI 评价生成失败，请重新回答",
            "reference_answer": "",
            "knowledge_gap": [],
            "next_question": "",
            "finished": False,
        }

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


def generate_next_question_simple(
    resume_data,
    question_type,
    previous_questions
):

    previous = "\n".join(
        previous_questions
    )


    prompt = f"""
你是一名技术面试官。

根据候选人简历生成一道面试题。

候选人信息：

{json.dumps(
    resume_data,
    ensure_ascii=False
)}


当前题型：

{question_type}


已经问过：

{previous}


要求：

1. 只生成一道问题
2. 必须和简历相关
3. 不要解释
4. 不要输出答案


直接输出问题。
"""


    response = client.chat.completions.create(

        model="glm-4.5",

        messages=[
            {
                "role":"user",
                "content":prompt
            }
        ],


        temperature=0.5,

        max_tokens=300
    )


    return response.choices[0].message.content.strip()





