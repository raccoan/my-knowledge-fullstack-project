from pypdf import  PdfReader

def extract_pdf_text(filepath:str):
    reader = PdfReader(filepath)
    text = ""
    for page in reader.pages:
        content = page.extract_text()
        if content:
            text+=content
    return text