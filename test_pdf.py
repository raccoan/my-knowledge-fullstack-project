from pypdf import PdfReader


filepath = "uploads/vue.pdf"

reader = PdfReader(filepath)

print("PDF页数：", len(reader.pages))

for i, page in enumerate(reader.pages):

    print("==============================")

    print("第", i + 1, "页")

    text = page.extract_text()

    print("提取结果：", repr(text))

    if text:
        print("文本长度：", len(text))
    else:
        print("这一页没有提取到文本")