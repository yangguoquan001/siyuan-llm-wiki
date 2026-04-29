"""Wiki 操作 — 通过思源笔记 API 读写页面、索引、日志。"""

from datetime import datetime
from siyuan_llm_wiki.siyuan import get_client, SiYuanError


PDF_PREFIX = "/pages/"


def _doc_path(page_name: str) -> str:
    """将页面名转为思源文档路径。name 如 'sources/source-xxx' → '/pages/sources/source-xxx'。"""
    clean = page_name.replace("\\", "/").strip("/")
    return f"{PDF_PREFIX}{clean}"


def _page_name_from_hpath(hpath: str) -> str:
    """从 SiYuan hpath 提取页面名（去掉 /pages/ 前缀）。"""
    if hpath.startswith(PDF_PREFIX) and hpath != PDF_PREFIX:
        return hpath[len(PDF_PREFIX) :]
    return ""


def init_wiki(raw_dir: str = "raw") -> None:
    """初始化 Wiki 结构：在思源笔记本中创建 schema/index/log 文档。"""
    from pathlib import Path
    import os

    client = get_client()

    for path, markdown in [
        ("/index", "# 索引\n"),
        ("/log", "# 操作日志\n"),
    ]:
        try:
            client.create_doc(path, markdown)
        except SiYuanError:
            pass

    raw = raw_dir or os.getenv("LLM_RAW_DIR", str(Path.cwd() / "raw"))
    Path(raw).mkdir(parents=True, exist_ok=True)


def read_page(name: str) -> str:
    """读取 wiki 页面内容。name 如 'sources/source-xxx'。"""
    client = get_client()
    ids = client.get_ids_by_hpath(_doc_path(name))
    if ids:
        return client.export_md_content(ids[0])
    return ""


def write_page(name: str, content: str) -> str:
    """写入 wiki 页面，不存在则创建，存在则更新。返回 block ID。"""
    client = get_client()
    path = _doc_path(name)
    ids = client.get_ids_by_hpath(path)

    if ids:
        block_id = ids[0]
        client.update_block(block_id, content)
        return block_id
    else:
        return client.create_doc(path, content)


def read_index() -> str:
    """读取索引文档。"""
    return _read_root_doc("index")


def write_index(content: str) -> str:
    """写入索引文档，返回 block ID。"""
    return _write_root_doc("index", content)


def read_log() -> str:
    """读取日志文档。"""
    return _read_root_doc("log")


def append_log(entry: str) -> None:
    """追加一条日志到日志文档。"""
    client = get_client()
    ids = client.get_ids_by_hpath("/log")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    line = f"## [{timestamp}] {entry}\n\n"

    if ids:
        current = client.export_md_content(ids[0])
        client.update_block(ids[0], current + line)
    else:
        client.create_doc("/log", f"# 操作日志\n\n{line}")


def list_pages() -> list[str]:
    """列出 /pages 下所有文档的相对路径名。"""
    client = get_client()
    try:
        rows = client.sql_query(
            "SELECT hpath FROM blocks "
            "WHERE type = 'd' AND hpath LIKE '/pages/%' "
            "AND hpath != '/pages/' "
            "ORDER BY hpath"
        )
    except SiYuanError:
        return []

    result = []
    for row in rows:
        name = _page_name_from_hpath(row.get("hpath", ""))
        if name:
            result.append(name)
    return result


def get_page_id(name: str) -> str:
    """获取页面在思源中的 block ID。"""
    client = get_client()
    ids = client.get_ids_by_hpath(_doc_path(name))
    return ids[0] if ids else ""


def get_all_page_ids() -> dict[str, str]:
    """获取所有 wiki 页面的 {页面名: block_id} 映射表。"""
    client = get_client()
    try:
        rows = client.sql_query(
            "SELECT id, hpath FROM blocks "
            "WHERE type = 'd' AND hpath LIKE '/pages/%' "
            "AND hpath != '/pages/'"
        )
    except SiYuanError:
        return {}

    mapping: dict[str, str] = {}
    for row in rows:
        bid = row.get("id", "")
        hpath = row.get("hpath", "")
        name = _page_name_from_hpath(hpath)
        if bid and name:
            mapping[name] = bid
    return mapping


def get_index_id() -> str:
    """获取索引文档的 block ID。"""
    client = get_client()
    ids = client.get_ids_by_hpath("/index")
    return ids[0] if ids else ""


def get_log_id() -> str:
    """获取日志文档的 block ID。"""
    client = get_client()
    ids = client.get_ids_by_hpath("/log")
    return ids[0] if ids else ""


# ── 内部辅助 ──


def _read_root_doc(name: str) -> str:
    client = get_client()
    ids = client.get_ids_by_hpath(f"/{name}")
    if ids:
        return client.export_md_content(ids[0])
    return ""


def _write_root_doc(name: str, content: str) -> str:
    client = get_client()
    ids = client.get_ids_by_hpath(f"/{name}")
    if ids:
        client.update_block(ids[0], content)
        return ids[0]
    else:
        return client.create_doc(f"/{name}", content)
