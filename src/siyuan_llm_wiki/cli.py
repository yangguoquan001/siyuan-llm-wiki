"""CLI 入口 — 提供 init/ingest/query/lint/chat 命令。"""

import os
import sys
import click
from pathlib import Path


@click.group()
@click.option(
    "--siyuan-url",
    envvar="SIYUAN_URL",
    default="http://127.0.0.1:6806",
    help="思源笔记 API 地址",
)
@click.option(
    "--siyuan-token", envvar="SIYUAN_TOKEN", default="", help="思源笔记 API Token"
)
@click.option(
    "--siyuan-notebook", envvar="SIYUAN_NOTEBOOK", default="", help="思源笔记本 ID"
)
@click.pass_context
def main(ctx, siyuan_url, siyuan_token, siyuan_notebook):
    """LLM Wiki — 基于 LLM 的个人知识库工具（思源笔记版）。

    将来源文档通过 LLM 深度整合到思源笔记中，构建可积累的结构化知识库。
    支持摄入来源文档、智能查询、健康检查。

    环境变量：
      LLM_PROVIDER       LLM 提供商 (openai/anthropic)，默认 openai
      LLM_MODEL          模型名称，默认 gpt-4o
      OPENAI_API_KEY     OpenAI API 密钥
      OPENAI_BASE_URL    OpenAI API 地址（可自定义）
      ANTHROPIC_API_KEY  Anthropic API 密钥
      SIYUAN_URL         思源笔记 API 地址，默认 http://127.0.0.1:6806
      SIYUAN_TOKEN       思源笔记 API Token
      SIYUAN_NOTEBOOK    思源笔记本 ID
      LLM_RAW_DIR        原始来源目录，默认 ./raw
    """
    from siyuan_llm_wiki.siyuan import set_config

    set_config(url=siyuan_url, token=siyuan_token, notebook=siyuan_notebook)
    ctx.ensure_object(dict)


@main.command()
@click.option("--raw-dir", "-r", default=None, help="原始来源目录路径")
@click.pass_context
def init(ctx, raw_dir):
    """初始化 Wiki 结构（在思源笔记本中创建必要文档）。"""
    from siyuan_llm_wiki.wiki import init_wiki
    from siyuan_llm_wiki.schema import write_default_schema

    raw = raw_dir or os.getenv("LLM_RAW_DIR", str(Path.cwd() / "raw"))
    init_wiki(raw)
    write_default_schema()

    click.echo("Wiki 已在思源笔记中初始化")
    click.echo("  结构约定：/schema")
    click.echo("  索引文件：/index")
    click.echo("  操作日志：/log")
    click.echo(f"来源目录：{raw}")
    click.echo()
    click.echo("下一步：将来源文档放入 raw/ 目录，然后运行 llm-wiki ingest <文件名>")


@main.command()
def notebooks():
    """列出思源笔记中所有笔记本及其 ID。"""
    from siyuan_llm_wiki.siyuan import list_notebooks

    try:
        nbs = list_notebooks()
    except Exception as e:
        click.echo(f"错误：{e}", err=True)
        raise SystemExit(1)

    if not nbs:
        click.echo("未找到任何笔记本。请在思源中创建笔记本后再试。")
        click.echo()
        click.echo(
            "提示：设置 SIYUAN_NOTEBOOK=<笔记本ID> 环境变量，或使用 --siyuan-notebook 选项。"
        )
        return

    click.echo(f"{'笔记本名称':<20} {'笔记本ID':<30} {'状态'}")
    click.echo("-" * 60)
    for nb in nbs:
        status = "已关闭" if nb.get("closed") else "已打开"
        click.echo(f"{nb.get('name', ''):<20} {nb.get('id', ''):<30} {status}")
    click.echo()
    click.echo("使用方法：设置环境变量 SIYUAN_NOTEBOOK=<笔记本ID>")
    click.echo('例如：$env:SIYUAN_NOTEBOOK = "20210817205410-2kvfpfn"')


@main.command()
@click.argument("source_file")
@click.option("--raw-dir", "-r", default=None, help="原始来源目录路径")
def ingest(source_file, raw_dir):
    """摄入一个来源文档，整合到 Wiki。

    SOURCE_FILE: 来源文件路径（支持 md/txt/pdf/html/docx/png/jpg）
    """
    raw = raw_dir or os.getenv("LLM_RAW_DIR", str(Path.cwd() / "raw"))

    from siyuan_llm_wiki.operations.ingest import run

    click.echo(f"正在处理：{source_file}")
    click.echo()

    try:
        result = run(source_file, raw)
        if result.get("summary"):
            click.echo(f"摘要：{result['summary']}")
        click.echo()
        click.echo(f"更新了 {len(result['changes'])} 个页面：")
        for change in result["changes"]:
            click.echo(f"  - {change}")
    except Exception as e:
        click.echo(f"错误：{e}", err=True)
        sys.exit(1)


@main.command()
@click.argument("question")
@click.option("--save", is_flag=True, help="将回答保存为 Wiki 页面")
def query(question, save):
    """查询 Wiki 知识库。

    QUESTION: 你要查询的问题
    """
    from siyuan_llm_wiki.operations.query import run

    click.echo(f"查询：{question}")
    click.echo()

    try:
        result = run(question, save=save)
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
def lint():
    """检查 Wiki 的健康状况。"""
    from siyuan_llm_wiki.operations.lint import run

    click.echo("正在进行 Wiki 健康检查...")
    click.echo()

    try:
        report = run()
        click.echo(report)
    except Exception as e:
        click.echo(f"错误：{e}", err=True)
        sys.exit(1)


@main.command()
def resolve():
    """将 index 中所有 [[页面名]] 转换为思源超链接。"""
    from siyuan_llm_wiki.wiki import read_index, get_index_id, get_page_id
    from siyuan_llm_wiki.siyuan import get_client
    from siyuan_llm_wiki.operations.ingest import _replace_wiki_links

    click.echo("正在解析 index 超链接...")

    index_id = get_index_id()
    if not index_id:
        click.echo("错误：index 文档不存在，请先运行 init 和 ingest。", err=True)
        sys.exit(1)

    content = read_index()
    if not content.strip():
        click.echo("index 为空，无需处理。")
        return

    import re
    refs = set()
    for m in re.finditer(r"\[\[(.+?)\]\]", content):
        refs.add(m.group(1))

    SUBDIRS = ["sources", "entities", "concepts", "comparisons", "overviews", "queries"]
    name_to_id: dict[str, str] = {}
    for name in refs:
        for subdir in SUBDIRS:
            path = f"{subdir}/{name}"
            bid = get_page_id(path)
            if bid:
                name_to_id[name] = bid
                break

    resolved = _replace_wiki_links(content, name_to_id)
    if resolved != content:
        client = get_client()
        client.update_block(index_id, resolved)
        resolved_count = sum(1 for name in refs if name in name_to_id)
        click.echo(f"完成。{resolved_count} 个链接已转换为 siyuan:// 格式。")
    else:
        click.echo("index 中没有需要转换的 [[链接]]。")


@main.command()
@click.option("--raw-dir", "-r", default=None, help="原始来源目录路径")
def chat(raw_dir):
    """交互式对话模式。"""
    raw = raw_dir or os.getenv("LLM_RAW_DIR", str(Path.cwd() / "raw"))

    from datetime import datetime
    from siyuan_llm_wiki import wiki, schema
    from siyuan_llm_wiki.llm import chat as llm_chat

    schema_content = schema.load_schema()
    index_content = wiki.read_index()

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

    click.echo("LLM Wiki 交互模式（思源笔记版）")
    click.echo('输入问题开始对话，输入 "exit" 或 "quit" 退出，输入 "help" 查看帮助。')
    click.echo()

    history: list[tuple[str, str]] = []  # [(role, content), ...]

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
            click.echo("  @save [标题] — 将当前对话保存为 Wiki 页面")
            click.echo("  exit / quit — 退出")
            click.echo()
            continue

        if user_input.lower().startswith("@ingest "):
            source_name = user_input[8:].strip()
            source_path = str(Path(raw) / source_name)
            if not Path(source_path).exists():
                click.echo(f"文件不存在：{source_path}")
                continue
            from siyuan_llm_wiki.operations.ingest import run as ingest_run

            click.echo("正在摄入...")
            result = ingest_run(source_path, raw)
            click.echo(f"完成。更新了 {len(result['changes'])} 个页面。")
            click.echo()
            continue

        if user_input.lower() == "@lint":
            from siyuan_llm_wiki.operations.lint import run as lint_run

            click.echo("正在检查...")
            report = lint_run()
            click.echo(report)
            click.echo()
            continue

        if user_input.lower().startswith("@save"):
            _do_save(history, user_input[5:].strip())
            continue

        click.echo()
        try:
            response = llm_chat(system_prompt, user_input)
            click.echo(response)
            history.append(("你", user_input))
            history.append(("助手", response))
        except Exception as e:
            click.echo(f"错误：{e}")
        click.echo()


def _do_save(history: list[tuple[str, str]], title: str = "") -> None:
    """将对话历史保存为 Wiki 查询存档页面。"""
    if not history:
        click.echo("对话历史为空，没有可保存的内容。")
        return

    from datetime import datetime
    from siyuan_llm_wiki import wiki

    timestamp = datetime.now().strftime("%Y%m%d-%H%M")
    safe_title = _make_safe_title(title) if title else f"对话-{timestamp}"
    page_name = f"queries/{safe_title}"

    lines = [f"# {title or f'对话存档 {timestamp}'}", ""]
    for role, text in history:
        lines.append(f"## {role}")
        lines.append("")
        lines.append(text)
        lines.append("")
    content = "\n".join(lines)

    wiki.write_page(page_name, content)
    wiki.append_log(f"chat | 对话已保存为 {page_name}")

    # 更新索引
    index_content = wiki.read_index()
    new_entry = f"- [[{safe_title}]]: 对话存档，{len(history) // 2} 轮问答\n"
    if "## 查询存档" not in index_content:
        index_content += "\n## 查询存档\n"
    index_content += new_entry
    wiki.write_index(index_content)

    click.echo(f"对话已保存到 /pages/{page_name}")


def _make_safe_title(text: str) -> str:
    import re
    safe = re.sub(r'[\\/*?:"<>|]', "", text)
    safe = re.sub(r"\s+", "-", safe)
    return safe[:40]
