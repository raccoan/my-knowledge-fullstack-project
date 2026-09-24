import os
import shutil
from datetime import datetime

from fastapi import APIRouter, Depends, UploadFile, File as FastAPIFile, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models.file import File
from models.document import Document
from models.chunk import Chunk
from schemas.document import DocumentDetailResponse

from utils.auth import get_current_user
from utils.pdf import extract_pdf_text
from utils.splitter import split_text
from utils.embedding import get_embedding
from utils.vector import add_vector, delete_vectors_by_document

from schemas.file import KnowledgeFileResponse


router = APIRouter(
    prefix="/files",
    tags=["files"]
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload")
def upload_file(
    file: UploadFile = FastAPIFile(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    user_id = current_user["id"]

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="目前只支持 PDF 文件"
        )

    safe_filename = file.filename

    file_path = os.path.join(
        UPLOAD_DIR,
        f"{user_id}_{safe_filename}"
    )

    document = None
    db_file = None

    try:
        # =========================
        # 1. 保存 PDF 文件
        # =========================
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        file_size = os.path.getsize(file_path)

        # =========================
        # 2. 创建 files 记录
        # =========================
        db_file = File(
            user_id=user_id,
            filename=safe_filename,
            file_path=file_path,
            file_size=file_size,
            created_time=datetime.now()
        )

        db.add(db_file)
        db.commit()
        db.refresh(db_file)

        # =========================
        # 3. 解析 PDF 文本
        # =========================
        text = extract_pdf_text(file_path)

        if not text.strip():
            raise Exception("PDF 中没有读取到有效文本")

        # =========================
        # 4. 创建 documents 记录
        # =========================
        document = Document(
            user_id=user_id,
            file_id=db_file.id,
            content=text,
            created_time=datetime.now(),
            status="processing",
            chunk_count=0
        )

        db.add(document)
        db.commit()
        db.refresh(document)

        # =========================
        # 5. 文本切分
        # =========================
        chunks = split_text(text)

        # =========================
        # 6. 保存 chunk + 生成向量
        # =========================
        for index, chunk_text in enumerate(chunks):

            chunk = Chunk(
                document_id=document.id,
                content=chunk_text,
                chunk_index=index
            )

            db.add(chunk)
            db.commit()
            db.refresh(chunk)

            embedding = get_embedding(chunk_text)

            add_vector(
                chunk_id=chunk.id,
                content=chunk_text,
                embedding=embedding,
                user_id=user_id,
                document_id=document.id
            )

        # =========================
        # 7. 更新文档状态
        # =========================
        document.status = "completed"
        document.chunk_count = len(chunks)

        db.add(document)
        db.commit()

        return {
            "message": "文件上传成功",
            "file_id": db_file.id,
            "document_id": document.id,
            "filename": safe_filename,
            "chunk_count": len(chunks),
            "status": "completed"
        }

    except Exception as e:
        db.rollback()

        # 如果已经创建了 document，尝试标记失败
        try:
            if document and document.id:
                document.status = "failed"
                db.add(document)
                db.commit()
        except Exception:
            db.rollback()

        # 删除本地文件
        if os.path.exists(file_path):
            os.remove(file_path)

        raise HTTPException(
            status_code=500,
            detail=f"文件处理失败：{str(e)}"
        )


@router.get("", response_model=list[KnowledgeFileResponse])
def get_files(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    user_id = current_user["id"]

    documents = (
        db.query(Document)
        .filter(Document.user_id == user_id)
        .order_by(Document.created_time.desc())
        .all()
    )

    result = []

    for document in documents:

        file = (
            db.query(File)
            .filter(
                File.id == document.file_id,
                File.user_id == user_id
            )
            .first()
        )

        result.append({
            "id": document.id,
            "file_id": document.file_id,
            "filename": file.filename if file else "",
            "status": document.status,
            "chunk_count": document.chunk_count,
            "file_size": file.file_size if file else None,
            "created_at": document.created_time
        })

    return result


@router.get("/{document_id}", response_model=DocumentDetailResponse)
def get_file_detail(
    document_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    user_id = current_user["id"]

    document = (
        db.query(Document)
        .filter(
            Document.id == document_id,
            Document.user_id == user_id
        )
        .first()
    )

    if not document:
        raise HTTPException(
            status_code=404,
            detail="文档不存在"
        )

    file = (
        db.query(File)
        .filter(
            File.id == document.file_id,
            File.user_id == user_id
        )
        .first()
    )

    chunks = (
        db.query(Chunk)
        .filter(
            Chunk.document_id == document.id
        )
        .order_by(Chunk.chunk_index.asc())
        .all()
    )

    return {
        "id": document.id,
        "file_id": document.file_id,
        "filename": file.filename if file else "",
        "file_size": file.file_size if file else None,
        "status": document.status,
        "chunk_count": document.chunk_count,
        "created_at": document.created_time,
        "chunks": [
            {
                "id": chunk.id,
                "chunk_index": chunk.chunk_index,
                "content": chunk.content
            }
            for chunk in chunks
        ]
    }




@router.delete("/{document_id}")
def delete_file(
    document_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    user_id = current_user["id"]

    document = (
        db.query(Document)
        .filter(
            Document.id == document_id,
            Document.user_id == user_id
        )
        .first()
    )

    if not document:
        raise HTTPException(
            status_code=404,
            detail="文档不存在"
        )

    file = (
        db.query(File)
        .filter(
            File.id == document.file_id,
            File.user_id == user_id
        )
        .first()
    )

    try:
        delete_vectors_by_document(
            document_id=document.id,
            user_id=user_id
        )
    except Exception as e:
        print(f"删除 Chroma 向量失败：{e}")

    (
        db.query(Chunk)
        .filter(Chunk.document_id == document.id)
        .delete(synchronize_session=False)
    )

    db.delete(document)

    if file:
        db.delete(file)

    db.commit()

    if file and file.file_path:
        if os.path.exists(file.file_path):
            os.remove(file.file_path)

    return {
        "message": "文档删除成功"
    }