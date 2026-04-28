"""健康检查操作 — 全面检查 Wiki 的问题和改进机会。"""

from llm_wiki import wiki, schema
from llm_wiki.llm import chat
from llm_wiki.prompts.lint import build_system_prompt, build_user_prompt


def run(wiki_dir: str) -> str:
    """执行健康检查，返回诊断报告。"""
    schema_content = schema.load_schema(wiki_dir)
    index_content = wiki.read_index(wiki_dir)
    log_content = wiki.read_log(wiki_dir)
    page_names = wiki.list_pages(wiki_dir)

    all_pages = [(name, wiki.read_page(wiki_dir, name)) for name in page_names]

    system_prompt = build_system_prompt(schema_content)
    user_prompt = build_user_prompt(all_pages, index_content, log_content)

    report = chat(system_prompt, user_prompt)

    wiki.append_log(wiki_dir, "lint | 执行健康检查")

    return report
