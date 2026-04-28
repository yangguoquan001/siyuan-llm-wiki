"""CLI 入口 — 提供 init/ingest/query/lint/chat 命令。"""

import os
import sys
import click
from pathlib import Path


def _get_wiki_raw_dirs(wiki_dir=None, raw_dir=None):
    """获取 wiki_dir 和 raw_dir，优先使用环境变量。"""
    wiki = wiki_dir or os.getenv("LLM_WIKI_DIR", str(Path.cwd() / "wiki"))
    raw = raw_dir or os.getenv("LLM_RAW_DIR", str(Path.cwd() / "raw"))
    return wiki, raw


@click.group()
def main():
    """LLM Wiki — 基于 LLM 的个人知识库工具。

    通过 LLM 增量构建和维护结构化 Wiki 知识库。
    支持摄入来源文档、智能查询、健康检查。

    环境变量：
      LLM_PROVIDER    LLM 提供商 (openai/anthropic)，默认 openai
      LLM_MODEL       模型名称，默认 gpt-4o
      OPENAI_API_KEY  OpenAI API 密钥
      ANTHROPIC_API_KEY Anthropic API 密钥
      LLM_WIKI_DIR    Wiki 目录，默认 ./wiki
      LLM_RAW_DIR     原始来源目录，默认 ./raw
    """
    pass


@main.command()
@click.option("--wiki-dir", "-w", default=None, help="Wiki 目录路径")
@click.option("--raw-dir", "-r", default=None, help="原始来源目录路径")
def init(wiki_dir, raw_dir):
    """初始化 Wiki 目录结构。"""
    wiki_dir, raw_dir = _get_wiki_raw_dirs(wiki_dir, raw_dir)

    from llm_wiki.wiki import init_wiki
    from llm_wiki.schema import write_default_schema

    init_wiki(wiki_dir, raw_dir)
    write_default_schema(wiki_dir)

    click.echo(f"Wiki 已初始化：{wiki_dir}")
    click.echo(f"  页面目录：{wiki_dir}/pages/")
    click.echo(f"  结构约定：{wiki_dir}/schema.md")
    click.echo(f"  索引文件：{wiki_dir}/index.md")
    click.echo(f"  操作日志：{wiki_dir}/log.md")
    click.echo(f"来源目录：{raw_dir}")
    click.echo()
    click.echo("下一步：将来源文档放入 raw/ 目录，然后运行 llm-wiki ingest <文件名>")


@main.command()
@click.argument("source_file")
@click.option("--wiki-dir", "-w", default=None, help="Wiki 目录路径")
@click.option("--raw-dir", "-r", default=None, help="原始来源目录路径")
def ingest(source_file, wiki_dir, raw_dir):
    """摄入一个来源文档，整合到 Wiki。

    SOURCE_FILE: 来源文件路径（支持 md/txt/pdf/html/docx/png/jpg）
    """
    wiki_dir, raw_dir = _get_wiki_raw_dirs(wiki_dir, raw_dir)

    from llm_wiki.operations.ingest import run

    click.echo(f"正在处理：{source_file}")
    click.echo()

    try:
        result = run(source_file, wiki_dir, raw_dir)
        if result.get("summary"):
            click.echo(f"摘要：{result['summary']}")
        click.echo()
        click.echo(f"更新了 {len(result['changes'])} 个文件：")
        for change in result["changes"]:
            click.echo(f"  - {change}")
    except Exception as e:
        click.echo(f"错误：{e}", err=True)
        sys.exit(1)


@main.command()
@click.argument("question")
@click.option("--save", is_flag=True, help="将回答保存为 Wiki 页面")
@click.option("--wiki-dir", "-w", default=None, help="Wiki 目录路径")
def query(question, save, wiki_dir):
    """查询 Wiki 知识库。

    QUESTION: 你要查询的问题
    """
    wiki_dir, _ = _get_wiki_raw_dirs(wiki_dir)

    from llm_wiki.operations.query import run

    click.echo(f"查询：{question}")
    click.echo()

    try:
        result = run(question, wiki_dir, save=save)
        click.echo(result["answer"])
        click.echo()
        if result["sources"]:
            click.echo("引用来源：")
            for src in result["sources"]:
                click.echo(f"  - [[{src}]]")
        if result["saved"]:
            click.echo(f"\n回答已保存为：{result['saved']}")
    except Exception as e:
        click.echo(f"错误：{e}", err=True)
        sys.exit(1)


@main.command()
@click.option("--wiki-dir", "-w", default=None, help="Wiki 目录路径")
def lint(wiki_dir):
    """检查 Wiki 的健康状况。"""
    wiki_dir, _ = _get_wiki_raw_dirs(wiki_dir)

    from llm_wiki.operations.lint import run

    click.echo("正在进行 Wiki 健康检查...")
    click.echo()

    try:
        report = run(wiki_dir)
        click.echo(report)
    except Exception as e:
        click.echo(f"错误：{e}", err=True)
        sys.exit(1)


@main.command()
@click.option("--wiki-dir", "-w", default=None, help="Wiki 目录路径")
@click.option("--raw-dir", "-r", default=None, help="原始来源目录路径")
def chat(wiki_dir, raw_dir):
    """交互式对话模式。"""
    wiki_dir, raw_dir = _get_wiki_raw_dirs(wiki_dir, raw_dir)

    from llm_wiki import wiki, schema
    from llm_wiki.llm import chat as llm_chat

    schema_content = schema.load_schema(wiki_dir)
    index_content = wiki.read_index(wiki_dir)

    system_prompt = f"""你是一个 Wiki 知识库维护助手。你可以帮助用户：
1. 回答关于 Wiki 内容的问题
2. 建议如何组织知识
3. 帮助摄入新来源（用户可以要求你处理 raw/ 目录中的文件）
4. 检查 Wiki 的健康状况

## Wiki 结构约定

{schema_content}

## 当前 Wiki 内容

{index_content}

请用中文回答。回答简洁明了。"""

    click.echo("LLM Wiki 交互模式")
    click.echo('输入问题开始对话，输入 "exit" 或 "quit" 退出，输入 "help" 查看帮助。')
    click.echo()

    while True:
        try:
            user_input = click.prompt("你", prompt_suffix=" > ").strip()
        except (EOFError, KeyboardInterrupt):
            click.echo("\n再见！")
            break

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit", "q"):
            click.echo("再见！")
            break

        if user_input.lower() == "help":
            click.echo("可用操作：")
            click.echo("  直接输入问题 — 查询 Wiki")
            click.echo("  @ingest <文件名> — 摄入 raw/ 中的文件")
            click.echo("  @lint — 执行健康检查")
            click.echo("  exit / quit — 退出")
            click.echo()
            continue

        if user_input.lower().startswith("@ingest "):
            source_name = user_input[8:].strip()
            source_path = str(Path(raw_dir) / source_name)
            if not Path(source_path).exists():
                click.echo(f"文件不存在：{source_path}")
                continue
            from llm_wiki.operations.ingest import run as ingest_run

            click.echo("正在摄入...")
            result = ingest_run(source_path, wiki_dir, raw_dir)
            click.echo(f"完成。更新了 {len(result['changes'])} 个文件。")
            click.echo()
            continue

        if user_input.lower() == "@lint":
            from llm_wiki.operations.lint import run as lint_run

            click.echo("正在检查...")
            report = lint_run(wiki_dir)
            click.echo(report)
            click.echo()
            continue

        click.echo()
        try:
            response = llm_chat(system_prompt, user_input)
            click.echo(response)
        except Exception as e:
            click.echo(f"错误：{e}")
        click.echo()


if __name__ == "__main__":
    main()
