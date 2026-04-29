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
    """从 index 中定位相关页面，再读取页面内容。"""
    index = wiki.read_index()
    if not index.strip():
        return []

    keywords = _extract_keywords(question)
    # 解析 index 中的每一行，提取 [[页面名]] 或 [页面名](siyuan://...) 格式
    refs = _parse_index_refs(index)

    # 按关键词匹配 index 条目
    matched = []
    for name, line_text in refs:
        if any(kw in line_text for kw in keywords) or not keywords:
            matched.append(name)

    # 去重，限制数量
    seen = set()
    results = []
    for name in matched:
        if name not in seen:
            seen.add(name)
            content = wiki.read_page(name)
            if content.strip():
                results.append((name, content))
            if len(results) >= 10:
                break

    # 无匹配时：返回所有非空页面（<=5 个时带内容）
    if not results:
        page_names = wiki.list_pages()
        for name in page_names[:10]:
            content = wiki.read_page(name)
            if content.strip():
                results.append((name, content))

    return results


def _parse_index_refs(index_content: str) -> list[tuple[str, str]]:
    """从 index 内容中解析出所有页面引用。
    
    index 中每行格式如：
    - [[GLU激活函数]]: 描述文字
    - [GLU激活函数](siyuan://blocks/xxx): 描述文字
    
    返回 [(页面名, 整行文本), ...]
    """
    refs = []
    for line in index_content.split("\n"):
        line = line.strip()
        if not line or not line.startswith("-"):
            continue
        # 匹配 [页面名](siyuan://...) 格式
        m = re.search(r"\[(.+?)\]\(siyuan://", line)
        if m:
            refs.append((m.group(1), line))
            continue
        # 匹配 [[页面名]] 格式
        m = re.search(r"\[\[(.+?)\]\]", line)
        if m:
            refs.append((m.group(1), line))
    return refs


def _extract_keywords(text: str) -> list[str]:
    """从问题中提取关键词：先按标点拆分，再对中文做 2-3 字滑动窗口补充。"""
    # 按标点/空白拆分
    tokens = re.split(r"[\s,，。！？、；：" "''（）\u3000]+", text)
    result = []
    for token in tokens:
        if len(token) >= 2:
            result.append(token)
        # 对含中文的 token 生成 2-3 字 ngram，提升召回
        cjk = re.findall(r"[\u4e00-\u9fff]+", token)
        for seg in cjk:
            for n in (2, 3):
                for i in range(len(seg) - n + 1):
                    result.append(seg[i : i + n])
    # 去重，限制数量
    seen = set()
    unique = []
    for w in result:
        if w not in seen:
            seen.add(w)
            unique.append(w)
    return unique[:15]


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
