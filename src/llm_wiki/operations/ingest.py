"""摄入操作 — 将来源文档整合到 Wiki 中。"""

import re
from pathlib import Path
from llm_wiki import wiki, schema, reader
from llm_wiki.llm import chat
from llm_wiki.prompts.ingest import build_system_prompt, build_user_prompt


def run(source_path: str, wiki_dir: str, raw_dir: str = "raw") -> dict:
    """执行摄入操作：读取来源 → 调用 LLM → 更新 Wiki。"""
    source_text = reader.read_file(source_path)
    file_name = Path(source_path).name
    schema_content = schema.load_schema(wiki_dir)
    index_content = wiki.read_index(wiki_dir)

    system_prompt = build_system_prompt(schema_content, wiki_dir)
    user_prompt = build_user_prompt(source_text, index_content, file_name)

    response = chat(system_prompt, user_prompt)

    ops = _parse_operations(response)
    changes = []
    for op in ops:
        if op["action"] == "update_index":
            wiki.write_index(wiki_dir, op["content"])
            changes.append("index.md")
        else:
            wiki.write_page(wiki_dir, op["path"], op["content"])
            changes.append(op["path"])

    log_entry = _extract_log_entry(response)
    wiki.append_log(wiki_dir, log_entry)

    return {
        "changes": changes,
        "summary": _extract_summary(response),
    }


def _parse_operations(response: str) -> list[dict]:
    """解析 LLM 响应中的文件操作指令。"""
    ops = []
    pattern = r"### (创建|更新) (pages/.+?\.md)\n(.*?)(?=\n### (?:创建|更新) |\n## 日志条目|\Z)"
    for match in re.finditer(pattern, response, re.DOTALL):
        action = "create" if match.group(1) == "创建" else "update"
        path = match.group(2).strip()
        content = match.group(3).strip()
        # 去除 pages/ 前缀 — write_page 会自动加上 pages/
        if path.startswith("pages/"):
            path = path[6:]
        # 去除内容外层包裹的 ```markdown 代码块
        content = _strip_markdown_fence(content)
        ops.append(
            {
                "action": action,
                "path": path,
                "content": content,
            }
        )

    idx_pattern = r"### (?:创建|更新) index\.md\n(.*?)(?=\n## 日志条目|\Z)"
    idx_match = re.search(idx_pattern, response, re.DOTALL)
    if idx_match:
        content = idx_match.group(1).strip()
        content = _strip_markdown_fence(content)
        ops.append({"action": "update_index", "content": content})

    return ops


def _strip_markdown_fence(text: str) -> str:
    """去除 LLM 可能包裹在内容外层的 ```markdown ... ``` 代码块。"""
    text = text.strip()
    if text.startswith("```markdown") or text.startswith("```md"):
        # 找到结尾的 ```
        end = text.rfind("```")
        if end > 0:
            # 跳过开头的 ```markdown 或 ```md 行
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
