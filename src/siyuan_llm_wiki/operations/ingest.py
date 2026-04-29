"""摄入操作 — 将来源文档整合到思源笔记 Wiki 中。"""

import re
from pathlib import Path
from siyuan_llm_wiki import wiki, schema, reader
from siyuan_llm_wiki.llm import chat
from siyuan_llm_wiki.prompts.ingest import build_system_prompt, build_user_prompt


def run(source_path: str, raw_dir: str = "raw") -> dict:
    """执行摄入操作：读取来源 → 调用 LLM → 更新思源 Wiki（含两遍超链接处理）。"""
    source_text = reader.read_file(source_path)
    file_name = Path(source_path).name
    return _ingest_text(source_text, file_name)


def run_text(source_text: str, source_name: str = "对话存档") -> dict:
    """用纯文本（非文件）执行摄入，用于保存对话等场景。"""
    return _ingest_text(source_text, source_name)


def _ingest_text(source_text: str, source_name: str) -> dict:
    """核心摄入逻辑：给定文本和来源名，执行 LLM 整合 + 超链接解析。"""
    schema_content = schema.load_schema()
    index_content = wiki.read_index()

    system_prompt = build_system_prompt(schema_content)
    user_prompt = build_user_prompt(source_text, index_content, source_name)

    response = chat(system_prompt, user_prompt)

    ops = _parse_operations(response)

    # ── 第一遍：创建/更新所有页面，收集 block ID ──
    page_ids: dict[str, str] = {}  # {页面名: block_id}
    index_id = ""
    changes = []

    for op in ops:
        if op["action"] == "update_index":
            index_id = wiki.write_index(op["content"])
            changes.append("index")
        else:
            bid = wiki.write_page(op["path"], op["content"])
            page_ids[op["path"]] = bid
            changes.append(op["path"])

    # ── 第二遍：替换 [[页面名]] 为 siyuan://blocks/{id} 超链接 ──
    if page_ids or index_id:
        _resolve_cross_references(page_ids, index_id)

    # ── 记录日志 ──
    log_entry = _extract_log_entry(response)
    wiki.append_log(log_entry)

    return {
        "changes": changes,
        "summary": _extract_summary(response),
    }


def _parse_operations(response: str) -> list[dict]:
    """解析 LLM 响应中的文档操作指令。"""
    ops = []
    # 匹配所有 ### 创建/更新 块
    pattern = r"### (创建|更新) (\S+)\n(.*?)(?=\n### (?:创建|更新) |\n## 日志条目|\Z)"
    for match in re.finditer(pattern, response, re.DOTALL):
        action_raw = match.group(1)
        path = match.group(2).strip()
        content = match.group(3).strip()
        content = _strip_markdown_fence(content)

        if path == "index":
            ops.append({"action": "update_index", "content": content})
        else:
            ops.append(
                {
                    "action": "create" if action_raw == "创建" else "update",
                    "path": path,
                    "content": content,
                }
            )

    return ops


def _resolve_cross_references(new_page_ids: dict[str, str], index_id: str) -> None:
    """第二遍：将 [[页面名]] 替换为 [页面名](siyuan://blocks/{id})。"""
    from siyuan_llm_wiki.siyuan import get_client

    client = get_client()

    name_to_id: dict[str, str] = {}

    # 1. 新创建/更新的页面
    for path, bid in new_page_ids.items():
        leaf = path.rsplit("/", 1)[-1] if "/" in path else path
        name_to_id[leaf] = bid

    # 2. 已有页面（通过 SQL 批量获取 + 逐个查找作为兜底）
    try:
        existing = wiki.get_all_page_ids()
    except Exception:
        existing = {}
    for path, bid in existing.items():
        leaf = path.rsplit("/", 1)[-1] if "/" in path else path
        if leaf not in name_to_id:
            name_to_id[leaf] = bid

    # 3. 新页面内容中的引用
    for path, bid in new_page_ids.items():
        content = wiki.read_page(path)
        if content:
            resolved = _replace_wiki_links(content, name_to_id)
            if resolved != content:
                client.update_block(bid, resolved)

    # 4. index 文档（最关键的解析步骤）
    if index_id:
        _resolve_index_links(client, index_id, name_to_id)


def _resolve_index_links(client, index_id: str, name_to_id: dict[str, str]) -> None:
    """解析 index 中的所有 [[页面名]] 为超链接，未命中时逐路径查找。"""
    SUBDIRS = ["sources", "entities", "concepts", "comparisons", "overviews", "queries"]

    content = wiki.read_index()
    if not content:
        return

    # 找出 index 中尚未映射的 [[页面名]]
    unresolved = set()
    for m in re.finditer(r"\[\[(.+?)\]\]", content):
        name = m.group(1)
        if name not in name_to_id:
            unresolved.add(name)

    # 逐个尝试子目录查找
    for name in unresolved:
        for subdir in SUBDIRS:
            bid = wiki.get_page_id(f"{subdir}/{name}")
            if bid:
                name_to_id[name] = bid
                break

    resolved = _replace_wiki_links(content, name_to_id)
    if resolved != content:
        client.update_block(index_id, resolved)


def _replace_wiki_links(content: str, name_to_id: dict[str, str]) -> str:
    """将内容中的 [[页面名]] 替换为 [页面名](siyuan://blocks/{id})。"""

    def replacer(m: re.Match) -> str:
        name = m.group(1)
        bid = name_to_id.get(name)
        if bid:
            return f"[{name}](siyuan://blocks/{bid})"
        # 尝试模糊匹配（检查是否有路径以 /name 结尾的）
        for path, pid in name_to_id.items():
            if path.endswith(f"/{name}"):
                return f"[{name}](siyuan://blocks/{pid})"
        return m.group(0)

    return re.sub(r"\[\[(.+?)\]\]", replacer, content)


def _strip_markdown_fence(text: str) -> str:
    """去除 LLM 可能包裹在内容外层的 ```markdown ... ``` 代码块。"""
    text = text.strip()
    if text.startswith("```markdown") or text.startswith("```md"):
        end = text.rfind("```")
        if end > 0:
            first_newline = text.find("\n")
            if first_newline > 0:
                text = text[first_newline + 1 : end].strip()
    elif text.startswith("```"):
        end = text.rfind("```")
        if end > 0 and end != 0:
            first_newline = text.find("\n")
            if first_newline > 0:
                text = text[first_newline + 1 : end].strip()
    return text


def _extract_log_entry(response: str) -> str:
    m = re.search(r"## 日志条目\n(.+)", response)
    return m.group(1).strip() if m else "ingest | 未知操作"


def _extract_summary(response: str) -> str:
    m = re.search(r"## 分析摘要\n(.+?)(?=\n## )", response, re.DOTALL)
    return m.group(1).strip() if m else ""
