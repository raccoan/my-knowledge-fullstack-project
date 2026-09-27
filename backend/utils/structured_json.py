"""
为 LLM 的 JSON 输出提供清洗、Pydantic 校验和有限重试。
"""

import json
from typing import Any, Callable, TypeVar

from pydantic import BaseModel, Field, ValidationError

T = TypeVar("T", bound=BaseModel)


class ResumeParseResult(BaseModel):
    basic_info: dict[str, Any] = Field(default_factory=dict)
    education: list[dict[str, Any]] = Field(default_factory=list)
    skills: list[Any] = Field(default_factory=list)
    projects: list[dict[str, Any]] = Field(default_factory=list)
    internships: list[dict[str, Any]] = Field(default_factory=list)
    self_evaluation: str = ""


class InterviewEvaluationResult(BaseModel):
    score: int = Field(ge=0, le=100)
    feedback: str = ""
    reference_answer: str = ""
    knowledge_gap: list[str] = Field(default_factory=list)
    next_question: str = ""
    finished: bool = False


def _extract_json(text: str) -> str:
    """清理 Markdown 包裹，并提取 JSON 对象。"""
    text = text.strip().replace("```json", "").replace("```", "").strip()

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1 or start > end:
        raise ValueError("模型返回中未找到 JSON 对象")

    return text[start : end + 1]


def request_validated_json(
    request_fn: Callable[[str], str],
    prompt: str,
    schema: type[T],
    max_attempts: int = 2,
) -> dict[str, Any]:
    """校验 LLM 输出；校验失败时最多重试一次。"""
    current_prompt = prompt
    last_error: Exception | None = None

    for _ in range(max_attempts):
        try:
            raw = request_fn(current_prompt)
            json_text = _extract_json(raw)

            return schema.model_validate(
                json.loads(json_text)
            ).model_dump()

        except (
            ValueError,
            json.JSONDecodeError,
            ValidationError,
        ) as exc:
            last_error = exc
            current_prompt = (
                f"{prompt}\n\n"
                "上一次输出无法通过 JSON 格式校验。"
                "请只返回符合既定字段和类型的 JSON，"
                "不要包含 Markdown 或解释。"
            )

    raise ValueError(
        f"LLM 结构化输出校验失败：{last_error}"
    )