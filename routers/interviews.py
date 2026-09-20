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

    # ============================================================
    # 获取历史薄弱知识点
    # ============================================================

    interviews = (
        db.query(Interview)
        .filter(
            Interview.user_id == user_id
        )
        .all()
    )

    interview_ids = [
        item.id
        for item in interviews
    ]

    weak_points = []

    if interview_ids:

        previous_messages = (
            db.query(InterviewMessage)
            .filter(
                InterviewMessage.interview_id.in_(
                    interview_ids
                ),
                InterviewMessage.role == "candidate"
            )
            .all()
        )

        for message in previous_messages:

            if not message.knowledge_gap:
                continue

            for gap in message.knowledge_gap:

                if gap and gap not in weak_points:
                    weak_points.append(gap)

    # ============================================================
    # 第一题使用“项目深挖”
    # ============================================================

    question = generate_interview_question(
        resume_data=resume.structured_data,
        weak_points=weak_points,
        question_type="项目深挖",
        previous_questions=[]
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
    next_question = ""

    # 保存本次回答的评价信息
    candidate_message.score = score
    candidate_message.feedback = feedback
    candidate_message.reference_answer = reference_answer
    candidate_message.knowledge_gap = knowledge_gap

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
                "reference_answer": item.reference_answer,
                "knowledge_gap": item.knowledge_gap,
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

    # ============================================================
    # 生成下一道面试题
    # ============================================================

    question_types = [
        "项目深挖",
        "技术原理",
        "项目结合技术原理",
        "实际场景",
        "薄弱知识点强化"
    ]

    # question_count 从 1 开始
    # 第一次回答完成后，下一题就是第 2 题
    next_question_index = question_count

    if next_question_index >= len(question_types):
        next_question_index = len(question_types) - 1

    question_type = question_types[
        next_question_index
    ]

    # ============================================================
    # 获取已经问过的问题
    # ============================================================

    previous_interviewer_messages = (
        db.query(InterviewMessage)
        .filter(
            InterviewMessage.interview_id == interview.id,
            InterviewMessage.role == "interviewer"
        )
        .order_by(
            InterviewMessage.created_at.asc()
        )
        .all()
    )

    previous_questions = [
        message.content
        for message in previous_interviewer_messages
    ]

    # ============================================================
    # 获取历史薄弱知识点
    # ============================================================

    interviews = (
        db.query(Interview)
        .filter(
            Interview.user_id == user_id
        )
        .all()
    )

    interview_ids = [
        item.id
        for item in interviews
    ]

    weak_points = []

    if interview_ids:

        previous_messages = (
            db.query(InterviewMessage)
            .filter(
                InterviewMessage.interview_id.in_(
                    interview_ids
                ),
                InterviewMessage.role == "candidate"
            )
            .all()
        )

        for message in previous_messages:

            if not message.knowledge_gap:
                continue

            for gap in message.knowledge_gap:

                if gap and gap not in weak_points:
                    weak_points.append(gap)

    # ============================================================
    # 生成下一题
    # ============================================================

    next_question = generate_interview_question(
        resume_data=resume.structured_data,
        weak_points=weak_points,
        question_type=question_type,
        previous_questions=previous_questions
    )

    # ============================================================
    # 保存下一道题
    # ============================================================

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
                "created_at": item.created_at,
                "knowledge_gap":item.knowledge_gap,
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


@router.get("/interviews")
def get_interviews(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    user_id = current_user["id"]

    interviews = (
        db.query(Interview)
        .filter(
            Interview.user_id == user_id
        )
        .order_by(
            Interview.created_at.desc()
        )
        .all()
    )

    return [
        {
            "id": interview.id,
            "resume_id": interview.resume_id,
            "status": interview.status,
            "total_score": interview.total_score,
            "created_at": interview.created_at,
            "updated_at": interview.updated_at
        }
        for interview in interviews
    ]

@router.get("/interviews/weak-points")
def get_weak_points(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    user_id = current_user["id"]

    # 1. 获取当前用户的所有面试
    interviews = (
        db.query(Interview)
        .filter(
            Interview.user_id == user_id
        )
        .all()
    )

    # 2. 获取这些面试的 ID
    interview_ids = [
        interview.id
        for interview in interviews
    ]

    # 3. 如果用户还没有进行过面试
    if not interview_ids:
        return {
            "knowledge_gaps": []
        }

    # 4. 获取这些面试中的所有候选人回答
    messages = (
        db.query(InterviewMessage)
        .filter(
            InterviewMessage.interview_id.in_(
                interview_ids
            ),
            InterviewMessage.role == "candidate"
        )
        .all()
    )

    # 5. 收集所有薄弱知识点
    knowledge_gaps = []

    for message in messages:

        # 当前回答没有薄弱知识点
        if not message.knowledge_gap:
            continue

        for gap in message.knowledge_gap:

            # 避免重复
            if gap and gap not in knowledge_gaps:
                knowledge_gaps.append(gap)

    return {
        "knowledge_gaps": knowledge_gaps
    }


