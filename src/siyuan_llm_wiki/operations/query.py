"""查询操作 — 基于思源笔记 Wiki 回答用户问题。"""

import re
from datetime import datetime
from siyuan_llm_wiki import wiki, schema
from siyuan_llm_wiki.llm import chat
from siyuan_llm_wiki.prompts.query import build_system_prompt, build_user_prompt, build_retrieval_prompt


def run(question: str, save: bool = False) -> dict:
    """执行查询操作。LLM 自行判断回答是否值得沉淀到 Wiki，自动 ingest。"""
    schema_content = schema.load_schema()
    index_content = wiki.read_index()

    relevant_pages = _find_relevant_pages(question)

    system_prompt = build_system_prompt(schema_content)
    user_prompt = build_user_prompt(question, relevant_pages)

    response = chat(system_prompt, user_prompt)

    answer = _extract_section(response, "回答")
    sources = _extract_sources(response)

    saved = None
    should_save = save or _llm_decides_to_save(response)
    if should_save and answer:
        saved = _ingest_query_result(question, response)

    wiki.append_log(f"query | {question[:60]}")

    return {"answer": answer, "sources": sources, "saved": saved}


def _find_relevant_pages(question: str) -> list[tuple[str, str]]:
    """由 LLM 根据 index 语义选出相关页面，再读取页面内容。"""
    index = wiki.read_index()
    if not index.strip():
        return []

    retrieval_prompt = build_retrieval_prompt(index, question)
    retrieval_response = chat(
        system_prompt="你是一个知识库检索助手。根据 index 和问题，选出最相关的页面。只输出页面名称，每行一个，不要任何解释。",
        user_prompt=retrieval_prompt,
    )

    page_names = _parse_retrieval_response(retrieval_response)
    if not page_names:
        return []

    results = []
    for name in page_names[:10]:
        content = wiki.read_page(name)
        if not content.strip():
            for sd in wiki.SUBDIRS:
                content = wiki.read_page(f"{sd}/{name}")
                if content.strip():
                    name = f"{sd}/{name}"
                    break
        if content.strip():
            results.append((name, content))

    return results


def _llm_decides_to_save(response: str) -> bool:
    """解析 LLM 输出中的 ## 保存判断 节。"""
    m = re.search(r"##\s*保存判断\s*[:：]?\s*(.+?)(?:\n|$)", response)
    if m:
        decision = m.group(1).strip().lower()
        return decision.startswith("yes")
    return False


def _ingest_query_result(question: str, response: str) -> str | None:
    """将查询问答原文通过 ingest 管线深度提取到 Wiki。"""
    from siyuan_llm_wiki.operations.ingest import run_text
    from siyuan_llm_wiki.wiki import make_safe_title

    timestamp = datetime.now().strftime("%Y%m%d-%H%M")
    safe_title = make_safe_title(question[:40])
    source_name = f"query-{safe_title}-{timestamp}"

    source_text = f"# 查询：{question}\n\n{response}"
    result = run_text(source_text, source_name)
    changes = result.get("changes", [])
    if changes:
        return changes[0]
    else:
        saved = f"queries/{source_name}"
        wiki.write_page(saved, response)
        return saved


def _parse_retrieval_response(response: str) -> list[str]:
    """解析 LLM 返回的页面名列表。"""
    names = []
    for line in response.strip().split("\n"):
        line = line.strip()
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
