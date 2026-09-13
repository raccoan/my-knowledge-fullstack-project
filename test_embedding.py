from utils.embedding import get_embedding


text = "Vue3中的ref用于创建响应式数据"


vector = get_embedding(text)


print("向量长度：", len(vector))
print("前10个向量：", vector[:10])