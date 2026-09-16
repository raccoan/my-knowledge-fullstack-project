from pydantic import BaseModel


class CreateInterviewRequest(BaseModel):
    resume_id: int


class AnswerInterviewRequest(BaseModel):
    answer: str


class InterviewAnswerResponse(BaseModel):
    score: int
    feedback: str
    next_question: str
    finished: bool