"""查询操作 — 基于 Wiki 回答用户问题。"""

import re
from datetime import datetime
from llm_wiki import wiki, schema
from llm_wiki.llm import chat
from llm_wiki.prompts.query import build_system_prompt, build_user_prompt


def run(question: str, wiki_dir: str, save: bool = False) -> dict:
    """执行查询操作。"""
    schema_content = schema.load_schema(wiki_dir)
    index_content = wiki.read_index(wiki_dir)
    page_names = wiki.list_pages(wiki_dir)

    relevant_pages = _find_relevant_pages(question, page_names, wiki_dir)

    system_prompt = build_system_prompt(schema_content)
    user_prompt = build_user_prompt(question, relevant_pages)

    response = chat(system_prompt, user_prompt)

    answer = _extract_section(response, "回答")
    sources = _extract_sources(response)

    saved = None
    if save and answer:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M")
        safe_title = _make_safe_title(question[:40])
        page_name = f"queries/query-{safe_title}-{timestamp}.md"
        wiki.write_page(wiki_dir, page_name, response)
        wiki.append_log(wiki_dir, f"query | {question[:50]} — 回答已保存为 {page_name}")

        index_content = wiki.read_index(wiki_dir)
        display_name = page_name.replace(".md", "").replace("queries/", "")
        new_entry = f"- [[{display_name}]]: {question[:60]}\n"
        if "## 查询存档" not in index_content:
            index_content += "\n## 查询存档\n"
        index_content += new_entry
        wiki.write_index(wiki_dir, index_content)
        saved = page_name

    return {"answer": answer, "sources": sources, "saved": saved}


def _find_relevant_pages(
    question: str, page_names: list[str], wiki_dir: str
) -> list[tuple[str, str]]:
    """简单关键词匹配找出相关页面。"""
    relevant = []
    for name in page_names:
        content = wiki.read_page(wiki_dir, name)
        question_set = set(question)
        name_set = set(name)
        if question_set & name_set or len(page_names) <= 5:
            relevant.append((name, content))
    return relevant[:10]


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
