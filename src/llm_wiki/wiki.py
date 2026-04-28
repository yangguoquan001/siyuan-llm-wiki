"""Wiki 文件系统操作 — 读写页面、索引、日志。"""

from pathlib import Path
from datetime import datetime


def init_wiki(wiki_dir: str, raw_dir: str) -> None:
    """初始化 Wiki 目录结构。"""
    wiki = Path(wiki_dir)
    wiki.mkdir(parents=True, exist_ok=True)
    (wiki / "pages").mkdir(exist_ok=True)
    (wiki / "schema.md").touch(exist_ok=True)
    (wiki / "index.md").touch(exist_ok=True)
    (wiki / "log.md").touch(exist_ok=True)
    Path(raw_dir).mkdir(parents=True, exist_ok=True)


def read_page(wiki_dir: str, page_name: str) -> str:
    """读取 wiki 页面内容，不存在则返回空字符串。"""
    path = Path(wiki_dir) / "pages" / page_name
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def write_page(wiki_dir: str, page_name: str, content: str) -> None:
    """写入 wiki 页面（先写临时文件再原子替换）。"""
    path = Path(wiki_dir) / "pages" / page_name
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def read_index(wiki_dir: str) -> str:
    """读取 index.md 内容，不存在则返回空字符串。"""
    path = Path(wiki_dir) / "index.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def write_index(wiki_dir: str, content: str) -> None:
    """写入 index.md（先写临时文件再原子替换）。"""
    path = Path(wiki_dir) / "index.md"
    tmp = path.with_suffix(".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def read_log(wiki_dir: str) -> str:
    """读取 log.md 内容，不存在则返回空字符串。"""
    path = Path(wiki_dir) / "log.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def append_log(wiki_dir: str, entry: str) -> None:
    """追加一条日志到 log.md。"""
    path = Path(wiki_dir) / "log.md"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    line = f"## [{timestamp}] {entry}\n\n"
    with open(path, "a", encoding="utf-8") as f:
        f.write(line)


def list_pages(wiki_dir: str) -> list[str]:
    """列出 pages/ 目录下所有 .md 文件的相对路径。"""
    pages_dir = Path(wiki_dir) / "pages"
    if not pages_dir.exists():
        return []
    return sorted(
        str(p.relative_to(pages_dir)).replace("\\", "/")
        for p in pages_dir.rglob("*.md")
    )
