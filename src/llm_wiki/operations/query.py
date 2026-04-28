"""查询操作 — 基于思源笔记 Wiki 回答用户问题。"""

import re
from datetime import datetime
from llm_wiki import wiki, schema
from llm_wiki.llm import chat
from llm_wiki.prompts.query import build_system_prompt, build_user_prompt
from llm_wiki.siyuan import get_client, SiYuanError


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
        timestamp = datetime.now().strftime("%Y%m%d-%H%M")
        safe_title = _make_safe_title(question[:40])
        page_name = f"queries/query-{safe_title}-{timestamp}"
        wiki.write_page(page_name, response)
        wiki.append_log(f"query | {question[:50]} — 回答已保存为 {page_name}")

        # 更新索引
        index_content = wiki.read_index()
        display_name = f"query-{safe_title}-{timestamp}"
        new_entry = f"- [[{display_name}]]: {question[:60]}\n"
        if "## 查询存档" not in index_content:
            index_content += "\n## 查询存档\n"
        index_content += new_entry
        wiki.write_index(index_content)
        saved = page_name

    return {"answer": answer, "sources": sources, "saved": saved}


def _find_relevant_pages(question: str) -> list[tuple[str, str]]:
    """通过思源 SQL 搜索相关页面。"""
    client = get_client()

    # 从问题中提取关键词用于 SQL LIKE 查询
    keywords = _extract_keywords(question)
    if not keywords:
        # 回退：列出所有页面
        page_names = wiki.list_pages()
        if len(page_names) <= 5:
            return [(n, wiki.read_page(n)) for n in page_names]
        return []

    # 构建 SQL 条件
    conditions = " OR ".join(f"content LIKE '%{kw}%'" for kw in keywords[:5])
    try:
        rows = client.sql_query(
            f"SELECT id, hpath FROM blocks "
            f"WHERE type = 'd' AND hpath LIKE '/pages/%' "
            f"AND ({conditions}) "
            f"LIMIT 10"
        )
    except SiYuanError:
        return []

    results = []
    seen = set()
    for row in rows:
        hpath = row.get("hpath", "")
        if hpath.startswith("/pages/") and hpath != "/pages/":
            name = hpath[len("/pages/") :]
            if name and name not in seen:
                seen.add(name)
                content = wiki.read_page(name)
                results.append((name, content))

    return results


def _extract_keywords(text: str) -> list[str]:
    """从问题中提取关键词用于 SQL 搜索。"""
    # 简单分词：按常见分隔符拆分，取长度 >= 2 的词
    words = re.split(r"[\s，。！？、；：" "''（）\u3000]+", text)
    return [w for w in words if len(w) >= 2][:10]


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
