import os

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
    text = extract_pdf_text(
        file_path
    )

    # 6. 保存数据库
    resume = Resume(
        user_id=user_id,
        filename=file.filename,
        file_path=file_path,
        content=text
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
            "created_at": resume.created_at,
            "updated_at": resume.updated_at
        }
        for resume in resumes
    ]