# 向量数据库

import chromadb

client = chromadb.PersistentClient(
    path = "./chroma"
)

collection = client.get_or_create_collection(
    name = "knowledge"
)

def add_vector(
        chunk_id,
        content,
        embedding,
        user_id,
        document_id
):
    collection.add(
        ids = [str(chunk_id)],
        documents = [content],
        embeddings = [embedding],
        metadatas=[{
            "user_id":user_id,
            "document_id":document_id
        }]
    )

def search_vector(
        query_embedding,
        user_id,
        n_results = 2,

):
    result = collection.query(
        query_embeddings = [query_embedding],
        n_results=n_results,
        where={"user_id":user_id},
        include=["documents","metadatas","distances"]
    )
    return  result

def delete_vectors_by_document(
        document_id:int,
        user_id:int
):
    collection.delete(
        where={
            "$and":[
                {
                    "document_id":document_id
                },
                {
                    "user_id":user_id
                }

            ]
        }
    )