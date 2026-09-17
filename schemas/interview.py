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
