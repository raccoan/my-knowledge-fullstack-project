import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from models.interview import Interview
from models.interview_message import InterviewMessage
from models.resume import Resume
from schemas.interview import (
    CreateInterviewRequest,
    AnswerInterviewRequest
)
from utils.auth import get_current_user
from utils.llm import (
    generate_interview_question,
    evaluate_interview_answer_with_knowledge,
    generate_interview_report
)
from utils.rag import retrieve_documents


router = APIRouter()


MAX_QUESTIONS = 5


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
            detail="该简历还没有完成结构化解析"
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

    if interview.status != "ongoing":
        raise HTTPException(
            status_code=400,
            detail="该面试已经结束"
        )

    if not request.answer.strip():
        raise HTTPException(
            status_code=400,
            detail="回答内容不能为空"
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

    # 保存候选人回答
    candidate_message = InterviewMessage(
        interview_id=interview.id,
        role="candidate",
        content=request.answer
    )

    db.add(candidate_message)
    db.commit()

    # 获取当前已经回答了多少道题
    question_count = (
        db.query(InterviewMessage)
        .filter(
            InterviewMessage.interview_id == interview.id,
            InterviewMessage.role == "candidate"
        )
        .count()
    )

    # 根据当前问题进行知识库检索
    knowledge_sources = retrieve_documents(
        interview.current_question,
        user_id,
        db
    )

    # AI评价回答
    result = evaluate_interview_answer_with_knowledge(
        resume_data=resume.structured_data,
        knowledge_sources=knowledge_sources,
        question=interview.current_question,
        answer=request.answer
    )

    score = int(result.get("score", 0))
    feedback = result.get("feedback", "")
    reference_answer = result.get(
        "reference_answer",
        ""
    )
    knowledge_gap = result.get(
        "knowledge_gap",
        []
    )
    next_question = result.get(
        "next_question",
        ""
    )

    # 保存本次回答的评价信息
    candidate_message.score = score
    candidate_message.feedback = feedback
    candidate_message.reference_answer = reference_answer

    db.add(candidate_message)

    # 第5题强制结束
    finished = question_count >= MAX_QUESTIONS

    if finished:
        interview.status = "finished"

        # 计算平均分
        scores = (
            db.query(InterviewMessage.score)
            .filter(
                InterviewMessage.interview_id == interview.id,
                InterviewMessage.role == "candidate",
                InterviewMessage.score.isnot(None)
            )
            .all()
        )

        score_values = [
            item[0]
            for item in scores
        ]

        if score_values:
            interview.total_score = round(
                sum(score_values) / len(score_values)
            )
        else:
            interview.total_score = 0

        interview.current_question = None

        db.commit()

        # 获取完整面试记录
        interview_messages = (
            db.query(InterviewMessage)
            .filter(
                InterviewMessage.interview_id == interview.id
            )
            .order_by(
                InterviewMessage.created_at.asc()
            )
            .all()
        )

        interview_records = [
            {
                "role": item.role,
                "content": item.content,
                "score": item.score,
                "feedback": item.feedback,
                "reference_answer": item.reference_answer
            }
            for item in interview_messages
        ]

        # 生成最终报告
        report = generate_interview_report(
            resume_data=resume.structured_data,
            interview_records=interview_records,
            knowledge_sources=knowledge_sources
        )

        interview.report = report

        db.commit()

        return {
            "score": score,
            "feedback": feedback,
            "reference_answer": reference_answer,
            "knowledge_gap": knowledge_gap,
            "next_question": "",
            "finished": True,
            "report": report
        }

    # 还没结束，继续下一题
    interview.current_question = next_question

    next_message = InterviewMessage(
        interview_id=interview.id,
        role="interviewer",
        content=next_question
    )

    db.add(next_message)

    db.commit()

    return {
        "score": score,
        "feedback": feedback,
        "reference_answer": reference_answer,
        "knowledge_gap": knowledge_gap,
        "next_question": next_question,
        "finished": False
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
                "reference_answer": item.reference_answer,
                "created_at": item.created_at
            }
            for item in messages
        ]
    }


@router.get("/interviews/{interview_id}/report")
def get_interview_report(
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

    if interview.status != "finished":
        raise HTTPException(
            status_code=400,
            detail="面试还没有结束"
        )

    return {
        "interview_id": interview.id,
        "total_score": interview.total_score,
        "report": interview.report
    }