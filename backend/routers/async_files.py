"""新增文件：backend/routers/async_files.py

新增的异步入库接口；不替换原有 /files/upload，同步上传仍可继续使用。
"""
import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File as FastAPIFile, HTTPException, UploadFile
from sqlalchemy.orm import Session

from database import SessionLocal, get_db
from models.chunk import Chunk
from models.document import Document
from models.file import File
from utils.auth import get_current_user
from utils.embedding import get_embedding
from utils.pdf import extract_pdf_text
from utils.splitter import split_text
from utils.vector import add_vector, delete_vectors_by_document

router = APIRouter(prefix="/files", tags=["async-files"])
UPLOAD_DIR = Path("uploads")


def _safe_pdf_name(filename: str | None) -> str:
    # 【新增：文件名安全处理】兼容 Windows/Linux 路径分隔符，防止路径穿越。
    name = (filename or "").replace("\\", "/").split("/")[-1]
    if not name or not name.lower().endswith(".pdf"):
        raise ValueError("目前只支持 PDF 文件")
    return name


def process_document_in_background(document_id: int, user_id: int) -> None:
    """【新增：后台任务】解析、切分和向量化，不占用上传请求。"""
    db = SessionLocal()
    try:
        document = db.query(Document).filter(Document.id == document_id, Document.user_id == user_id).first()
        if not document:
            return
        file = db.query(File).filter(File.id == document.file_id, File.user_id == user_id).first()
        if not file:
            raise RuntimeError("文件记录不存在")

        text = extract_pdf_text(file.file_path)
        if not text.strip():
            raise RuntimeError("PDF 中没有读取到有效文本")

        # 重试时先清理旧分块与旧向量，避免重复入库。
        delete_vectors_by_document(document_id=document.id, user_id=user_id)
        db.query(Chunk).filter(Chunk.document_id == document.id).delete(synchronize_session=False)

        chunks = split_text(text)
        chunk_rows = [Chunk(document_id=document.id, content=item, chunk_index=index) for index, item in enumerate(chunks)]
        db.add_all(chunk_rows)
        db.flush()  # 一次拿到所有 chunk id，避免旧代码中逐条 commit。

        for row in chunk_rows:
            add_vector(
                chunk_id=row.id,
                content=row.content,
                embedding=get_embedding(row.content),
                user_id=user_id,
                document_id=document.id,
            )

        document.content = text
        document.chunk_count = len(chunk_rows)
        document.status = "completed"
        db.commit()
    except Exception as exc:
        db.rollback()
        # 【新增：失败状态】保留原文件，以便用户调用 retry 接口重试。
        try:
            delete_vectors_by_document(document_id=document_id, user_id=user_id)
            db.query(Chunk).filter(Chunk.document_id == document_id).delete(synchronize_session=False)
            db.query(Document).filter(Document.id == document_id, Document.user_id == user_id).update(
                {"status": "failed", "chunk_count": 0}, synchronize_session=False
            )
            db.commit()
        except Exception:
            db.rollback()
        print(f"文档 {document_id} 后台处理失败：{exc}")
    finally:
        db.close()


@router.post("/upload-async", status_code=202)
def upload_file_async(
    background_tasks: BackgroundTasks,
    file: UploadFile = FastAPIFile(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """【新增接口】快速返回，实际入库工作交给 BackgroundTasks。"""
    try:
        filename = _safe_pdf_name(file.filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    user_id = current_user["id"]
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    # UUID 避免同名文件覆盖。
    file_path = UPLOAD_DIR / f"{user_id}_{uuid.uuid4().hex}_{filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    db_file = File(user_id=user_id, filename=filename, file_path=str(file_path), file_size=os.path.getsize(file_path), created_time=datetime.now())
    db.add(db_file)
    db.flush()
    document = Document(user_id=user_id, file_id=db_file.id, content="", created_time=datetime.now(), status="processing", chunk_count=0)
    db.add(document)
    db.commit()
    db.refresh(document)

    background_tasks.add_task(process_document_in_background, document.id, user_id)
    return {"message": "文件已接收，正在后台入库", "document_id": document.id, "status": document.status}


@router.get("/processing/{document_id}")
def get_processing_status(document_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """【新增接口】供前端轮询 processing / completed / failed 状态。"""
    document = db.query(Document).filter(Document.id == document_id, Document.user_id == current_user["id"]).first()
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    return {"document_id": document.id, "status": document.status, "chunk_count": document.chunk_count}


@router.post("/{document_id}/retry", status_code=202)
def retry_document(document_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """【新增接口】仅允许失败任务重新入队。"""
    user_id = current_user["id"]
    document = db.query(Document).filter(Document.id == document_id, Document.user_id == user_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    if document.status != "failed":
        raise HTTPException(status_code=409, detail="仅失败文档允许重试")
    document.status = "processing"
    db.commit()
    background_tasks.add_task(process_document_in_background, document.id, user_id)
    return {"message": "已重新加入处理队列", "document_id": document.id, "status": "processing"}
