from test_search import query_embedding, result
from utils.embedding import get_embedding
from utils.vector import search_vector
from utils.llm import chat_with_llm,chat_with_llm_stream


def rag_answer(question: str,user_id:int):

    # 1. 用户问题转成向量
    query_embedding = get_embedding(question)


    # 2. 从Chroma搜索相关内容
    result = search_vector(
        query_embedding,
        user_id,
        n_results=3
    )


    # 3. 获取搜索到的文本
    documents = result["documents"][0]
    distances = result["distances"][0]
    metadatas = result["metadatas"][0]

    print("问题：",question)
    print("距离：",distances)
    print("来源：", metadatas)


    # 4. 拼接上下文
    context = "\n\n".join(documents)


    # 5. 构造Prompt
    prompt = f"""
你是一个知识库问答助手。

请严格根据下面的知识库内容回答问题。

如果知识库中没有相关信息，请明确告诉用户“知识库中没有找到相关信息”，不要自己编造答案。

知识库内容：

{context}


用户问题：

{question}
"""


    # 6. 调用大模型
    answer = chat_with_llm(prompt)


    return {
        "answer":answer,
        "metadatas":metadatas
    }


def rag_answer_stream(question:str,user_id:int):
    print("开始rag stream")
    # 将问题转换为向量
    stream_query_embedding = get_embedding(question)
    print("embedding完成")
    #搜索用户当前知识库
    stream_result = search_vector(stream_query_embedding,user_id,n_results=3)
    print("chroma查询完成")
    print("stream_result:",stream_result)
    # 获取相关文档
    stream_documents = stream_result["documents"][0]
    print("stream_documents:",stream_documents)
    # 拼接知识库内容
    stream_context = "\n\n".join(stream_documents)
    #构造propmt
    prompt = f"""
    你是一个知识库问答助手。

    请严格根据下面的知识库内容回答问题。

    如果知识库中没有相关信息，请明确告诉用户：
    “知识库中没有找到相关信息”。

    不要自己编造答案。

    知识库内容：

    {stream_context}

    用户问题：

    {question}
    """

    print("开始调用流式LLM")
    # 6. 调用流式大模型
    for content in chat_with_llm_stream(prompt):
        print("RAG收到内容：",content)
        yield content
    print("RAG STREAM结束")
