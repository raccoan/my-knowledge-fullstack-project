from pydantic import BaseModel


class CreateInterviewRequest(BaseModel):
    resume_id: int


class AnswerInterviewRequest(BaseModel):
    answer: str


class InterviewAnswerResponse(BaseModel):
    score: int
    feedback: str
    reference_answer:str
    knowledge_gap:list[str]
    next_question: str
    finished: bool

class InterviewReportResponse(BaseModel):
    overall_score: int
    project_ability: int
    technical_ability: int
    practical_ability: int
    communication_ability: int

    strengths: list[str]
    weaknesses: list[str]
    knowledge_gaps: list[str]
    suggestions: list[str]