import os
import time

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Depends,
    HTTPException
)

from sqlalchemy.orm import Session

from database import get_db
from models.resume import Resume
from utils.auth import get_current_user
from utils.pdf import extract_pdf_text
from utils.llm import parse_resume_with_llm


router = APIRouter()


UPLOAD_DIR = "uploads/resumes"

os.makedirs(
    UPLOAD_DIR,
    exist_ok=True
)


@router.post("/resumes/upload")
def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    # 1. 检查文件类型
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="目前只支持PDF文件"
        )

    # 2. 获取当前用户
    user_id = current_user["id"]

    # 3. 保存路径
    file_path = os.path.join(
        UPLOAD_DIR,
        file.filename
    )

    # 4. 保存 PDF
    with open(
        file_path,
        "wb"
    ) as f:
        f.write(
            file.file.read()
        )

    # 5. 解析 PDF

    print("开始解析 PDF")

    pdf_start = time.time()

    text = extract_pdf_text(file_path)

    pdf_time = time.time() - pdf_start

    print("PDF解析完成")
    print(
        "PDF解析耗时:",
        pdf_time,
        "秒"
    )

    print(
        "简历文本长度:",
        len(text)
    )

    print("开始调用 LLM 解析简历")

    llm_start = time.time()

    structured_data = parse_resume_with_llm(text)

    llm_time = time.time() - llm_start

    print("LLM简历解析完成")

    print(
        "LLM解析耗时:",
        llm_time,
        "秒"
    )
    # 6. 保存数据库
    resume = Resume(
        user_id=user_id,
        filename=file.filename,
        file_path=file_path,
        content=text,
        structured_data=structured_data
    )

    db.add(resume)

    db.commit()

    db.refresh(resume)

    # 7. 返回结果
    return {
        "message": "简历上传成功",
        "resume": {
            "id": resume.id,
            "filename": resume.filename,
            "file_path": resume.file_path,
            "structured_data": resume.structured_data,
            "created_at": resume.created_at,
            "updated_at": resume.updated_at
        }
    }


@router.get("/resumes")
def get_resumes(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    user_id = current_user["id"]

    resumes = (
        db.query(Resume)
        .filter(
            Resume.user_id == user_id
        )
        .order_by(
            Resume.created_at.desc()
        )
        .all()
    )

    return [
        {
            "id": resume.id,
            "filename": resume.filename,
            "file_path": resume.file_path,
            "structured_data":resume.structured_data,
            "created_at": resume.created_at,
            "updated_at": resume.updated_at,
        }
        for resume in resumes
    ]






