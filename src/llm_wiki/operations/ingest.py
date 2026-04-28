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
    pattern = r"### (创建|更新) (pages/.+?\.md)\n(.*?)(?=\n### |\n## |\Z)"
    for match in re.finditer(pattern, response, re.DOTALL):
        action = "create" if match.group(1) == "创建" else "update"
        ops.append(
            {
                "action": action,
                "path": match.group(2).strip(),
                "content": match.group(3).strip(),
            }
        )

    idx_pattern = r"### 更新 index\.md\n(.*?)(?=\n## 日志条目|\n## \Z|\Z)"
    idx_match = re.search(idx_pattern, response, re.DOTALL)
    if idx_match:
        ops.append({"action": "update_index", "content": idx_match.group(1).strip()})

    return ops


def _extract_log_entry(response: str) -> str:
    m = re.search(r"## 日志条目\n(.+)", response)
    return m.group(1).strip() if m else "ingest | 未知操作"


def _extract_summary(response: str) -> str:
    m = re.search(r"## 分析摘要\n(.+?)(?=\n## )", response, re.DOTALL)
    return m.group(1).strip() if m else ""
