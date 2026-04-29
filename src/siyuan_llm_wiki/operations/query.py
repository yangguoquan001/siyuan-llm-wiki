"""查询操作 — 基于思源笔记 Wiki 回答用户问题。"""

import re
from datetime import datetime
from siyuan_llm_wiki import wiki, schema
from siyuan_llm_wiki.llm import chat
from siyuan_llm_wiki.prompts.query import build_system_prompt, build_user_prompt


def run(question: str, save: bool = False) -> dict:
    """执行查询操作。"""
    schema_content = schema.load_schema()
    index_content = wiki.read_index()

    relevant_pages = _find_relevant_pages(question)

    system_prompt = build_system_prompt(schema_content)
    user_prompt = build_user_prompt(question, relevant_pages)

    response = chat(system_prompt, user_prompt)

    answer = _extract_section(response, "回答")
    sources = _extract_sources(response)

    saved = None
    if save and answer:
        from siyuan_llm_wiki.operations.ingest import run_text

        timestamp = datetime.now().strftime("%Y%m%d-%H%M")
        safe_title = _make_safe_title(question[:40])
        source_name = f"query-{safe_title}-{timestamp}"

        # 将问答原文格式化为来源文本，交给 ingest 做深度提取
        source_text = f"# 查询：{question}\n\n{response}"
        result = run_text(source_text, source_name)
        changes = result.get("changes", [])
        if changes:
            saved = changes[0]  # 第一个通常是来源摘要页
        else:
            # ingest 未产生变化时，直接保存原文
            saved = f"queries/{source_name}"
            wiki.write_page(saved, response)

    return {"answer": answer, "sources": sources, "saved": saved}


def _find_relevant_pages(question: str) -> list[tuple[str, str]]:
    """由 LLM 根据 index 语义选出相关页面，再读取页面内容。"""
    index = wiki.read_index()
    if not index.strip():
        return []

    # 第一次 LLM 调用：让 LLM 从 index 中选出相关页面
    retrieval_prompt = _build_retrieval_prompt(index, question)
    retrieval_response = chat(
        system_prompt="你是一个知识库检索助手。根据 index 和问题，选出最相关的页面。只输出页面名称，每行一个，不要任何解释。",
        user_prompt=retrieval_prompt,
    )

    page_names = _parse_retrieval_response(retrieval_response)
    if not page_names:
        return []

    # 读取选中的页面内容
    results = []
    for name in page_names[:10]:
        content = wiki.read_page(name)
        if content.strip():
            results.append((name, content))

    return results


def _build_retrieval_prompt(index: str, question: str) -> str:
    return f"""以下是 Wiki 知识库的索引。每行格式为：`- [[页面名]]: 一句话描述`。

{index}

---

用户问题：{question}

请从索引中选出与问题最相关的页面（最多 10 个），每个一行，只输出页面名：
entities/xxx
concepts/xxx
sources/xxx"""


def _parse_retrieval_response(response: str) -> list[str]:
    """解析 LLM 返回的页面名列表。"""
    names = []
    for line in response.strip().split("\n"):
        line = line.strip()
        # 跳过编号前缀如 "1. " 或 "- "
        line = re.sub(r"^\d+[\.\)、]\s*", "", line)
        line = line.lstrip("- ").strip()
        if line:
            names.append(line)
    return names


def _extract_section(response: str, section: str) -> str:
    m = re.search(rf"## {section}\n(.*?)(?=\n## |\Z)", response, re.DOTALL)
    return m.group(1).strip() if m else response


def _extract_sources(response: str) -> list[str]:
    sources = []
    m = re.search(r"## 引用来源\n(.*?)(?=\n## |\Z)", response, re.DOTALL)
    if m:
        for line in m.group(1).strip().split("\n"):
            match = re.search(r"\[\[(.+?)\]\]", line)
            if match:
                sources.append(match.group(1))
    return sources


def _make_safe_title(text: str) -> str:
    """将问题转为安全的文件名片段。"""
    safe = re.sub(r'[\\/*?:"<>|]', "", text)
    safe = re.sub(r"\s+", "-", safe)
    return safe[:40]
