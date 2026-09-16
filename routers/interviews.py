from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from sqlalchemy.orm import Session

from database import get_db

from models.resume import Resume
from models.interview import Interview
from models.interview_message import InterviewMessage

from schemas.interview import (
    CreateInterviewRequest,
    AnswerInterviewRequest
)

from utils.auth import get_current_user
from utils.llm import (
    generate_interview_question,
    evaluate_interview_answer
)


router = APIRouter()


@router.post("/interviews")
def create_interview(
    request: CreateInterviewRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    user_id = current_user["id"]

    resume = (
        db.query(Resume)
        .filter(
            Resume.id == request.resume_id,
            Resume.user_id == user_id
        )
        .first()
    )

    if not resume:
        raise HTTPException(
            status_code=404,
            detail="简历不存在"
        )

    if not resume.structured_data:
        raise HTTPException(
            status_code=400,
            detail="该简历还没有完成AI解析"
        )

    question = generate_interview_question(
        resume.structured_data
    )

    interview = Interview(
        user_id=user_id,
        resume_id=resume.id,
        status="ongoing",
        current_question=question,
        total_score=0
    )

    db.add(interview)
    db.commit()
    db.refresh(interview)

    message = InterviewMessage(
        interview_id=interview.id,
        role="interviewer",
        content=question
    )

    db.add(message)
    db.commit()

    return {
        "id": interview.id,
        "resume_id": interview.resume_id,
        "status": interview.status,
        "question": question
    }


@router.post("/interviews/{interview_id}/answer")
def answer_interview(
    interview_id: int,
    request: AnswerInterviewRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    user_id = current_user["id"]

    interview = (
        db.query(Interview)
        .filter(
            Interview.id == interview_id,
            Interview.user_id == user_id
        )
        .first()
    )

    if not interview:
        raise HTTPException(
            status_code=404,
            detail="面试不存在"
        )

    if interview.status == "finished":
        raise HTTPException(
            status_code=400,
            detail="该面试已经结束"
        )

    resume = (
        db.query(Resume)
        .filter(
            Resume.id == interview.resume_id,
            Resume.user_id == user_id
        )
        .first()
    )

    if not resume:
        raise HTTPException(
            status_code=404,
            detail="简历不存在"
        )

    question = interview.current_question

    user_message = InterviewMessage(
        interview_id=interview.id,
        role="candidate",
        content=request.answer
    )

    db.add(user_message)

    result = evaluate_interview_answer(
        resume.structured_data,
        question,
        request.answer
    )

    score = result["score"]
    feedback = result["feedback"]
    next_question = result["next_question"]
    finished = result["finished"]

    assistant_message = InterviewMessage(
        interview_id=interview.id,
        role="interviewer",
        content=next_question,
        score=score,
        feedback=feedback
    )

    db.add(assistant_message)

    interview.total_score = (
        interview.total_score + score
    )

    if finished:
        interview.status = "finished"
        interview.current_question = None
    else:
        interview.current_question = next_question

    db.commit()

    return {
        "score": score,
        "feedback": feedback,
        "next_question": next_question,
        "finished": finished
    }


@router.get("/interviews/{interview_id}")
def get_interview(
    interview_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    user_id = current_user["id"]

    interview = (
        db.query(Interview)
        .filter(
            Interview.id == interview_id,
            Interview.user_id == user_id
        )
        .first()
    )

    if not interview:
        raise HTTPException(
            status_code=404,
            detail="面试不存在"
        )

    messages = (
        db.query(InterviewMessage)
        .filter(
            InterviewMessage.interview_id == interview.id
        )
        .order_by(
            InterviewMessage.created_at.asc()
        )
        .all()
    )

    return {
        "id": interview.id,
        "resume_id": interview.resume_id,
        "status": interview.status,
        "total_score": interview.total_score,
        "current_question": interview.current_question,
        "messages": [
            {
                "id": item.id,
                "role": item.role,
                "content": item.content,
                "score": item.score,
                "feedback": item.feedback,
                "created_at": item.created_at
            }
            for item in messages
        ]
    }