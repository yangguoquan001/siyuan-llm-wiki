"""多格式文件读取器 — 将各种格式统一转换为纯文本。"""

from pathlib import Path


def read_file(file_path: str) -> str:
    """根据文件扩展名自动选择读取方式，返回纯文本内容。"""
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext in (".md", ".txt"):
        return path.read_text(encoding="utf-8")
    elif ext == ".pdf":
        return _read_pdf(path)
    elif ext in (".html", ".htm"):
        return _read_html(path)
    elif ext == ".docx":
        return _read_docx(path)
    elif ext in (".png", ".jpg", ".jpeg", ".gif", ".webp"):
        return _read_image(path)
    else:
        raise ValueError(f"不支持的文件格式: {ext}")


def _read_pdf(path: Path) -> str:
    import pdfplumber

    texts = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                texts.append(text)
    return "\n\n".join(texts)


def _read_html(path: Path) -> str:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    return soup.get_text("\n", strip=True)


def _read_docx(path: Path) -> str:
    from docx import Document

    doc = Document(str(path))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def _read_image(path: Path) -> str:
    from llm_wiki.llm import chat_with_image

    prompt = "请详细描述这张图片中的所有文字内容和视觉信息。请优先提取图中可见的所有文字，包括标题、标注、数据等。"
    return chat_with_image(prompt, str(path))
