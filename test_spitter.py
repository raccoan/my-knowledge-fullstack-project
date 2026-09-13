from utils.pdf import extract_pdf_text
from utils.splitter import split_text


filepath = "uploads/西南大学-2027届-刘倩-前端实习生.pdf"

# 1. 读取PDF
text = extract_pdf_text(filepath)

print("原始文本长度：", len(text))


# 2. 切分文本
chunks = split_text(text)

print("chunk数量：", len(chunks))


# 3. 查看每一个chunk
for i, chunk in enumerate(chunks):

    print("==============================")

    print("chunk索引：", i)

    print("chunk长度：", len(chunk))

    print("chunk内容：")

    print(chunk)