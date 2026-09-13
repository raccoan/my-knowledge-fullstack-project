from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Depends,
    HTTPException
)
from sqlalchemy.orm import Session
from database import get_db
from models.file import File as FileModel
from utils.auth import get_current_user
from utils.pdf import extract_pdf_text
from models.document import Document
from models.chunk import Chunk
from utils.splitter import split_text
from utils.embedding import get_embedding
from utils.vector import add_vector,delete_vectors_by_document
from models.user import User

import os



router = APIRouter()

UPLOAD_DIR = "uploads"

# 上传文件
@router.post("/files/upload")
def upload_file(
        file: UploadFile = File(...),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="目前只支持PDF文件"
        )

    os.makedirs(
        UPLOAD_DIR,
        exist_ok=True
    )

    file_path = f"{UPLOAD_DIR}/{file.filename}"

    with open(
        file_path,
        "wb"
    ) as f:
        f.write(
            file.file.read()
        )

    db_file = FileModel(
        filename=file.filename,
        file_path=file_path,
        user_id=current_user["id"]
    )

    db.add(db_file)
    db.commit()
    db.refresh(db_file)

    text = extract_pdf_text(file_path)

    document = Document(
        file_id=db_file.id,
        content=text
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    chunks = split_text(text)

    for chunk in chunks:
        db_chunk = Chunk(
            document_id=document.id,
            content=chunk
        )

        db.add(db_chunk)
        db.flush()

        embedding = get_embedding(chunk)

        add_vector(
            db_chunk.id,
            chunk,
            embedding,
            current_user["id"],
            document.id
        )

    db.commit()

    return {
        "message": "上传成功",
        "file": {
            "id": db_file.id,
            "filename": db_file.filename,
            "filepath": db_file.file_path
        }
    }


# 获取用户文件列表
@router.get("/files")
def get_files(
        db: Session = Depends(get_db),
        current_user=Depends(get_current_user)
):
    files = db.query(FileModel).filter(
        FileModel.user_id == current_user["id"]
    ).all()

    return files


# 删除接口
@router.delete("/files/{file_id}")
def delete_file(
        file_id: int,
        db: Session = Depends(get_db),
        current_user=Depends(get_current_user)
):
    user_id=current_user["id"]
    file = db.query(FileModel).filter(
        FileModel.id == file_id,
        FileModel.user_id == user_id
    ).first()

    if not file:
        raise HTTPException(
            status_code=404,
            detail="文件不存在"
        )

    file_path = file.file_path

    document = db.query(Document).filter(
        Document.file_id == file.id
    ).first()

    if document:
        # 删除chroma向量
        delete_vectors_by_document(
            document.id,
            user_id
        )

        # 删除Chunk
        db.query(Chunk).filter(
            Chunk.document_id == document.id
        ).delete(
            synchronize_session=False
        )

        # 删除document
        db.delete(document)

    # 删除file
    db.delete(file)

    db.commit()


    # 删除本地磁盘pdf
    if file_path and os.path.exists(file_path):
        os.remove(file_path)

    return {
        "message": "删除成功"
    }