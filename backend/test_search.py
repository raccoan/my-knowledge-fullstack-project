from utils.vector import search_vector
from utils.embedding import get_embedding

question = "vue3与vue2的区别"

query_embedding = get_embedding(question)
result = search_vector(
    query_embedding,
    n_results=3,
    user_id=1
)

print("搜索结果：")
for document in result["documents"][0]:
    print("---------")
    print(document)