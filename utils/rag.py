from sqlalchemy.orm import Session

from utils.embedding import get_embedding
from utils.vector import search_vector
from utils.llm import chat_with_llm
from utils.llm import chat_with_llm_stream

from models.document import Document
from models.file import File as FileModel


def retrieve_documents(
        question: str,
        user_id: int,
        db: Session
):
    """
    根据问题，从当前用户自己的知识库中检索相关知识。
    """

    query_embedding = get_embedding(question)

    result = search_vector(
        query_embedding,
        user_id,
        n_results=3
    )

    documents = result.get(
        "documents",
        [[]]
    )[0]

    metadatas = result.get(
        "metadatas",
        [[]]
    )[0]

    distances = result.get(
        "distances",
        [[]]
    )[0]

    sources = []

    for index, content in enumerate(documents):

        metadata = metadatas[index]

        document_id = metadata[
            "document_id"
        ]

        document = db.query(
            Document
        ).filter(
            Document.id == document_id
        ).first()

        filename = "未知文件"

        if document:

            file = db.query(
                FileModel
            ).filter(
                FileModel.id == document.file_id
            ).first()

            if file:
                filename = file.filename

        sources.append({
            "document_id": document_id,
            "filename": filename,
            "content": content,
            "distance": distances[index]
        })

    return sources


def build_prompt(
        question: str,
        sources: list
):
    context = "\n\n".join(
        [
            source["content"]
            for source in sources
        ]
    )

    prompt = f"""
你是一个基于用户个人知识库进行回答的 AI 助手。

请严格根据下面提供的知识库内容回答问题。

如果知识库中没有足够的信息，请明确告诉用户：
“知识库中没有找到足够的信息。”

不要编造知识库中不存在的内容。

知识库内容：
----------------
{context}
----------------

用户问题：
{question}
"""

    return prompt


def rag_answer(
        question: str,
        user_id: int,
        db: Session
):
    sources = retrieve_documents(
        question,
        user_id,
        db
    )

    prompt = build_prompt(
        question,
        sources
    )

    answer = chat_with_llm(
        prompt
    )

    return {
        "answer": answer,
        "sources": sources
    }


def rag_answer_stream(
        question: str,
        user_id: int,
        db: Session
):
    sources = retrieve_documents(
        question,
        user_id,
        db
    )

    prompt = build_prompt(
        question,
        sources
    )

    for content in chat_with_llm_stream(
        prompt
    ):
        yield content