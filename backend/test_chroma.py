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

print("数量：", len(result["ids"]))

for i in range(min(3, len(result["ids"]))):
    print("ID：", result["ids"][i])
    print("文本：", result["documents"][i])
    print("向量前10个：", result["embeddings"][i][:10])
    print("----------------")