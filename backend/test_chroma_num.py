import chromadb


client = chromadb.PersistentClient(
    path="./chroma"
)

collection = client.get_collection(
    name="knowledge"
)


result = collection.get(
    include=["documents", "embeddings"]
)


print("Chroma中的chunk数量：", len(result["ids"]))


for i in range(len(result["ids"])):

    print("==============================")

    print("ID：", result["ids"][i])

    print("完整文本：")
    print(result["documents"][i])

    print("向量维度：")
    print(len(result["embeddings"][i]))

    print("向量前10个：")
    print(result["embeddings"][i][:10])