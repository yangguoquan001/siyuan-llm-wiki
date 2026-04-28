# LLM Wiki 工具 — 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个 Python CLI 工具，基于 LLM Wiki 方法论，通过 LLM 增量构建和维护个人知识库（Wiki）。

**Architecture:** 全 LLM 驱动方案。工具负责文件 I/O 编排和 Prompt 管理，所有语义理解（摘要、交叉引用、矛盾检测）由 LLM 完成。模块分为：wiki 文件系统、reader 多格式解析、llm 客户端、prompts 模板、operations 编排、CLI 入口。

**Tech Stack:** Python 3.11+, uv, Click, openai SDK, anthropic SDK, pdfplumber, beautifulsoup4, python-docx, Pillow, pytest

---

### Task 1: 项目初始化

**Files:**
- Create: `pyproject.toml`
- Create: `src/llm_wiki/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: 编写 pyproject.toml**

```toml
[project]
name = "llm-wiki"
version = "0.1.0"
description = "基于 LLM Wiki 方法论的个人知识库工具"
requires-python = ">=3.11"
dependencies = [
    "click>=8.1",
    "openai>=1.0",
    "anthropic>=0.40",
    "pdfplumber>=0.11",
    "beautifulsoup4>=4.12",
    "python-docx>=1.1",
    "pillow>=10.0",
]

[project.scripts]
llm-wiki = "llm_wiki.cli:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 2: 使用 uv 初始化项目**

```bash
uv init --no-readme --no-pin-python
```

- [ ] **Step 3: 创建 `__init__.py` 文件**

```python
# src/llm_wiki/__init__.py (empty)
```

```python
# tests/__init__.py (empty)
```

- [ ] **Step 4: 安装依赖**

```bash
uv sync
```

- [ ] **Step 5: 提交**

```bash
git add pyproject.toml uv.lock src/ tests/
git commit -m "chore: 初始化项目结构和依赖"
```

---

### Task 2: Schema 模块

**Files:**
- Create: `src/llm_wiki/schema.py`
- Create: `tests/test_schema.py`

- [ ] **Step 1: 编写测试**

```python
# tests/test_schema.py
import tempfile
from pathlib import Path
from llm_wiki.schema import load_schema, write_default_schema, DEFAULT_SCHEMA


def test_default_schema_is_chinese():
    assert "Wiki 结构约定" in DEFAULT_SCHEMA
    assert "页面类型" in DEFAULT_SCHEMA
    assert "来源摘要页" in DEFAULT_SCHEMA
    assert "交叉引用" in DEFAULT_SCHEMA


def test_load_schema_returns_default_when_no_file():
    with tempfile.TemporaryDirectory() as tmp:
        result = load_schema(tmp)
        assert result == DEFAULT_SCHEMA


def test_load_schema_returns_file_content():
    with tempfile.TemporaryDirectory() as tmp:
        schema_path = Path(tmp) / "schema.md"
        schema_path.write_text("# 自定义 Schema", encoding="utf-8")
        result = load_schema(tmp)
        assert result == "# 自定义 Schema"


def test_write_default_schema_creates_file():
    with tempfile.TemporaryDirectory() as tmp:
        write_default_schema(tmp)
        schema_path = Path(tmp) / "schema.md"
        assert schema_path.exists()
        content = schema_path.read_text(encoding="utf-8")
        assert "Wiki 结构约定" in content


def test_write_default_schema_does_not_overwrite():
    with tempfile.TemporaryDirectory() as tmp:
        schema_path = Path(tmp) / "schema.md"
        schema_path.write_text("# 我的自定义 Schema", encoding="utf-8")
        write_default_schema(tmp)
        assert schema_path.read_text(encoding="utf-8") == "# 我的自定义 Schema"
```

- [ ] **Step 2: 运行测试确认失败**

```bash
uv run pytest tests/test_schema.py -v
```
Expected: ModuleNotFoundError

- [ ] **Step 3: 实现 schema.py**

```python
"""Schema 管理 — 加载和生成 Wiki 结构约定文档。"""
from pathlib import Path

DEFAULT_SCHEMA = """# Wiki 结构约定

## 页面类型

- **来源摘要页**: 以 `source-` 为前缀，记录单个来源文档的关键信息，包括：标题、来源、日期、关键要点、与已有知识的关联
- **实体页**: 以实体名称为标题，记录关于某个实体（人、组织、地点、概念等）的所有已知信息
- **概念页**: 记录某个概念或主题的深入分析，综合多个来源的观点
- **对比页**: 以 `对比-` 为前缀，对比两个或多个实体/概念的异同
- **综合页**: 以 `综述-` 为前缀，对某个领域的整体性概述

## 页面命名规范

- 使用中文命名，简洁明了
- 来源摘要页: `source-来源名称.md`
- 实体页: `实体名称.md`
- 概念页: `概念名称.md`
- 页面之间使用 `[[页面名]]` 进行交叉引用

## 页面结构规范

每个页面应包含：
1. 页面标题（一级标题）
2. 内容正文，分段组织
3. 底部：相关页面链接列表

## 索引规范

index.md 按类别组织，格式如下：

```
# 索引

## 来源
- [[source-xxx]]: 一句话描述

## 实体
- [[实体名]]: 一句话描述

## 概念
- [[概念名]]: 一句话描述
```
"""


def load_schema(wiki_dir: str) -> str:
    """加载 Wiki 目录中的 schema.md，如果不存在或为空则返回默认 schema。"""
    path = Path(wiki_dir) / "schema.md"
    if path.exists():
        content = path.read_text(encoding="utf-8").strip()
        if content:
            return content
    return DEFAULT_SCHEMA


def write_default_schema(wiki_dir: str) -> None:
    """如果 schema.md 不存在或为空，写入默认 schema。"""
    path = Path(wiki_dir) / "schema.md"
    if not path.exists() or not path.read_text(encoding="utf-8").strip():
        path.write_text(DEFAULT_SCHEMA, encoding="utf-8")
```

- [ ] **Step 4: 运行测试确认通过**

```bash
uv run pytest tests/test_schema.py -v
```
Expected: 5 passed

- [ ] **Step 5: 提交**

```bash
git add src/llm_wiki/schema.py tests/test_schema.py
git commit -m "feat: 添加 schema 模块，支持默认中文 schema 模板"
```

---

### Task 3: Wiki 文件系统模块

**Files:**
- Create: `src/llm_wiki/wiki.py`
- Create: `tests/test_wiki.py`

- [ ] **Step 1: 编写测试**

```python
# tests/test_wiki.py
import tempfile
from pathlib import Path
from llm_wiki.wiki import (
    init_wiki,
    read_page,
    write_page,
    read_index,
    write_index,
    append_log,
    read_log,
    list_pages,
)


class TestInitWiki:
    def test_creates_directories_and_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            wiki_dir = str(Path(tmp) / "wiki")
            raw_dir = str(Path(tmp) / "raw")
            init_wiki(wiki_dir, raw_dir)
            assert Path(wiki_dir).is_dir()
            assert (Path(wiki_dir) / "pages").is_dir()
            assert (Path(wiki_dir) / "schema.md").exists()
            assert (Path(wiki_dir) / "index.md").exists()
            assert (Path(wiki_dir) / "log.md").exists()
            assert Path(raw_dir).is_dir()

    def test_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            wiki_dir = str(Path(tmp) / "wiki")
            raw_dir = str(Path(tmp) / "raw")
            init_wiki(wiki_dir, raw_dir)
            init_wiki(wiki_dir, raw_dir)  # 不应报错
            assert Path(wiki_dir).is_dir()


class TestPageOperations:
    def test_write_and_read_page(self):
        with tempfile.TemporaryDirectory() as tmp:
            wiki_dir = str(Path(tmp) / "wiki")
            init_wiki(wiki_dir, str(Path(tmp) / "raw"))
            write_page(wiki_dir, "test.md", "# 测试页面\n内容")
            content = read_page(wiki_dir, "test.md")
            assert content == "# 测试页面\n内容"

    def test_write_page_subdirectory(self):
        with tempfile.TemporaryDirectory() as tmp:
            wiki_dir = str(Path(tmp) / "wiki")
            init_wiki(wiki_dir, str(Path(tmp) / "raw"))
            write_page(wiki_dir, "sub/dir/test.md", "# 子目录测试")
            content = read_page(wiki_dir, "sub/dir/test.md")
            assert content == "# 子目录测试"

    def test_read_nonexistent_page_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            wiki_dir = str(Path(tmp) / "wiki")
            init_wiki(wiki_dir, str(Path(tmp) / "raw"))
            assert read_page(wiki_dir, "nonexistent.md") == ""


class TestIndexOperations:
    def test_write_and_read_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            wiki_dir = str(Path(tmp) / "wiki")
            init_wiki(wiki_dir, str(Path(tmp) / "raw"))
            write_index(wiki_dir, "# 索引\n- [[page1]]")
            assert read_index(wiki_dir) == "# 索引\n- [[page1]]"


class TestLogOperations:
    def test_append_and_read_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            wiki_dir = str(Path(tmp) / "wiki")
            init_wiki(wiki_dir, str(Path(tmp) / "raw"))
            append_log(wiki_dir, "ingest | 测试文档")
            log = read_log(wiki_dir)
            assert "ingest | 测试文档" in log

    def test_multiple_entries(self):
        with tempfile.TemporaryDirectory() as tmp:
            wiki_dir = str(Path(tmp) / "wiki")
            init_wiki(wiki_dir, str(Path(tmp) / "raw"))
            append_log(wiki_dir, "ingest | 文档A")
            append_log(wiki_dir, "query | 问题B")
            log = read_log(wiki_dir)
            assert "文档A" in log
            assert "问题B" in log


class TestListPages:
    def test_list_pages(self):
        with tempfile.TemporaryDirectory() as tmp:
            wiki_dir = str(Path(tmp) / "wiki")
            init_wiki(wiki_dir, str(Path(tmp) / "raw"))
            write_page(wiki_dir, "a.md", "# A")
            write_page(wiki_dir, "sub/b.md", "# B")
            pages = list_pages(wiki_dir)
            assert set(pages) == {"a.md", "sub/b.md"}

    def test_list_pages_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            wiki_dir = str(Path(tmp) / "wiki")
            init_wiki(wiki_dir, str(Path(tmp) / "raw"))
            assert list_pages(wiki_dir) == []
```

- [ ] **Step 2: 运行测试确认失败**

```bash
uv run pytest tests/test_wiki.py -v
```
Expected: ImportError / all fail

- [ ] **Step 3: 实现 wiki.py**

```python
"""Wiki 文件系统操作 — 读写页面、索引、日志。"""
from pathlib import Path
from datetime import datetime


def init_wiki(wiki_dir: str, raw_dir: str) -> None:
    """初始化 Wiki 目录结构。"""
    wiki = Path(wiki_dir)
    wiki.mkdir(parents=True, exist_ok=True)
    (wiki / "pages").mkdir(exist_ok=True)
    (wiki / "schema.md").touch(exist_ok=True)
    (wiki / "index.md").touch(exist_ok=True)
    (wiki / "log.md").touch(exist_ok=True)
    Path(raw_dir).mkdir(parents=True, exist_ok=True)


def read_page(wiki_dir: str, page_name: str) -> str:
    """读取 wiki 页面内容，不存在则返回空字符串。"""
    path = Path(wiki_dir) / "pages" / page_name
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def write_page(wiki_dir: str, page_name: str, content: str) -> None:
    """写入 wiki 页面（先写临时文件再原子替换）。"""
    path = Path(wiki_dir) / "pages" / page_name
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def read_index(wiki_dir: str) -> str:
    """读取 index.md 内容，不存在则返回空字符串。"""
    path = Path(wiki_dir) / "index.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def write_index(wiki_dir: str, content: str) -> None:
    """写入 index.md（先写临时文件再原子替换）。"""
    path = Path(wiki_dir) / "index.md"
    tmp = path.with_suffix(".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def read_log(wiki_dir: str) -> str:
    """读取 log.md 内容，不存在则返回空字符串。"""
    path = Path(wiki_dir) / "log.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def append_log(wiki_dir: str, entry: str) -> None:
    """追加一条日志到 log.md。"""
    path = Path(wiki_dir) / "log.md"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    line = f"## [{timestamp}] {entry}\n\n"
    with open(path, "a", encoding="utf-8") as f:
        f.write(line)


def list_pages(wiki_dir: str) -> list[str]:
    """列出 pages/ 目录下所有 .md 文件的相对路径。"""
    pages_dir = Path(wiki_dir) / "pages"
    if not pages_dir.exists():
        return []
    return sorted(
        str(p.relative_to(pages_dir)).replace("\\", "/")
        for p in pages_dir.rglob("*.md")
    )
```

- [ ] **Step 4: 运行测试确认通过**

```bash
uv run pytest tests/test_wiki.py -v
```
Expected: all tests pass

- [ ] **Step 5: 提交**

```bash
git add src/llm_wiki/wiki.py tests/test_wiki.py
git commit -m "feat: 添加 wiki 文件系统模块，支持页面/索引/日志的读写"
```

---

### Task 4: LLM 客户端模块

**Files:**
- Create: `src/llm_wiki/llm.py`
- Create: `tests/test_llm.py`

- [ ] **Step 1: 编写测试**

```python
# tests/test_llm.py
import os
from unittest.mock import patch, MagicMock
from llm_wiki.llm import chat, get_client


class TestGetClient:
    def test_openai_client(self):
        with patch.dict(os.environ, {"LLM_PROVIDER": "openai", "OPENAI_API_KEY": "sk-test"}):
            with patch("llm_wiki.llm.OpenAI") as mock_openai:
                get_client()
                mock_openai.assert_called_once()

    def test_anthropic_client(self):
        with patch.dict(os.environ, {"LLM_PROVIDER": "anthropic", "ANTHROPIC_API_KEY": "sk-test"}):
            with patch("llm_wiki.llm.Anthropic") as mock_anthropic:
                get_client()
                mock_anthropic.assert_called_once()

    def test_invalid_provider_raises(self):
        with patch.dict(os.environ, {"LLM_PROVIDER": "invalid"}):
            try:
                get_client()
                assert False, "应该抛出异常"
            except ValueError as e:
                assert "不支持的 LLM 提供商" in str(e)


class TestChat:
    def test_chat_openai(self):
        with patch.dict(os.environ, {"LLM_PROVIDER": "openai", "OPENAI_API_KEY": "sk-test"}):
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "你好，这是回复"
            mock_client.chat.completions.create.return_value = mock_response

            with patch("llm_wiki.llm.get_client", return_value=mock_client):
                result = chat("你是一个助手", "你好")
                assert result == "你好，这是回复"

    def test_chat_anthropic(self):
        with patch.dict(os.environ, {"LLM_PROVIDER": "anthropic", "ANTHROPIC_API_KEY": "sk-test"}):
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.content = [MagicMock()]
            mock_response.content[0].text = "你好，这是 Claude 的回复"
            mock_client.messages.create.return_value = mock_response

            with patch("llm_wiki.llm.get_client", return_value=mock_client):
                result = chat("你是一个助手", "你好")
                assert result == "你好，这是 Claude 的回复"

    def test_chat_retry_on_failure(self):
        with patch.dict(os.environ, {"LLM_PROVIDER": "openai", "OPENAI_API_KEY": "sk-test"}):
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "重试后成功"

            mock_client.chat.completions.create.side_effect = [
                Exception("API 错误"),
                Exception("API 错误"),
                mock_response,
            ]

            with patch("llm_wiki.llm.get_client", return_value=mock_client):
                result = chat("你是一个助手", "你好")
                assert result == "重试后成功"
                assert mock_client.chat.completions.create.call_count == 3
```

- [ ] **Step 2: 运行测试确认失败**

```bash
uv run pytest tests/test_llm.py -v
```
Expected: ImportError

- [ ] **Step 3: 实现 llm.py**

```python
"""LLM 客户端抽象 — 统一 OpenAI 和 Anthropic 接口。"""
import os
import time
from openai import OpenAI
from anthropic import Anthropic

MAX_RETRIES = 3
RETRY_BASE_DELAY = 1.0


def get_client():
    """根据 LLM_PROVIDER 环境变量返回对应的客户端实例。"""
    provider = os.getenv("LLM_PROVIDER", "openai")
    if provider == "openai":
        return OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        )
    elif provider == "anthropic":
        return Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    else:
        raise ValueError(f"不支持的 LLM 提供商: {provider}")


def chat(system_prompt: str, user_prompt: str, model: str | None = None) -> str:
    """发送对话请求，自动重试。"""
    provider = os.getenv("LLM_PROVIDER", "openai")
    model = model or os.getenv("LLM_MODEL", "gpt-4o")
    client = get_client()

    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            if provider == "openai":
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                )
                return response.choices[0].message.content or ""
            elif provider == "anthropic":
                response = client.messages.create(
                    model=model,
                    max_tokens=8192,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}],
                )
                content = response.content
                return content[0].text if content else ""
        except Exception as e:
            last_error = e
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_BASE_DELAY * (2 ** attempt))
            continue

    raise RuntimeError(f"LLM API 调用失败（重试 {MAX_RETRIES} 次后）: {last_error}")


def chat_with_image(system_prompt: str, image_path: str, model: str | None = None) -> str:
    """发送含图片的对话请求（仅支持 OpenAI 视觉模型）。"""
    import base64
    from pathlib import Path

    provider = os.getenv("LLM_PROVIDER", "openai")
    model = model or os.getenv("LLM_MODEL", "gpt-4o")
    client = get_client()

    image_bytes = Path(image_path).read_bytes()
    ext = Path(image_path).suffix.lower()
    mime_type = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg"}.get(
        ext.lstrip("."), "image/png"
    )
    base64_image = base64.b64encode(image_bytes).decode("utf-8")

    for attempt in range(MAX_RETRIES):
        try:
            if provider == "anthropic":
                response = client.messages.create(
                    model=model,
                    max_tokens=4096,
                    system=system_prompt,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": mime_type,
                                        "data": base64_image,
                                    },
                                },
                                {"type": "text", "text": system_prompt},
                            ],
                        }
                    ],
                )
                return response.content[0].text if response.content else ""
            else:
                # OpenAI vision
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": system_prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:{mime_type};base64,{base64_image}",
                                        "detail": "auto",
                                    },
                                },
                            ],
                        },
                    ],
                )
                return response.choices[0].message.content or ""
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_BASE_DELAY * (2 ** attempt))
                continue
            raise RuntimeError(f"图片识别 LLM API 调用失败: {e}")
```

- [ ] **Step 4: 运行测试确认通过**

```bash
uv run pytest tests/test_llm.py -v
```
Expected: all tests pass

- [ ] **Step 5: 提交**

```bash
git add src/llm_wiki/llm.py tests/test_llm.py
git commit -m "feat: 添加 LLM 客户端模块，支持 OpenAI 和 Anthropic，含重试逻辑"
```

---

### Task 5: Reader 多格式文件读取器

**Files:**
- Create: `src/llm_wiki/reader.py`
- Create: `tests/test_reader.py`
- Create: `tests/fixtures/sample.md`
- Create: `tests/fixtures/sample.txt`
- Create: `tests/fixtures/sample.html`

- [ ] **Step 1: 创建测试 fixtures**

```markdown
# tests/fixtures/sample.md
# 测试标题

这是测试内容。
```

```
# tests/fixtures/sample.txt
纯文本测试内容。
```

```html
<!-- tests/fixtures/sample.html -->
<html>
<head><title>测试</title></head>
<body>
<article>
<h1>HTML 测试</h1>
<p>这是 HTML 中的正文内容。</p>
</article>
<script>console.log("应被移除")</script>
<style>body { color: red; }</style>
</body>
</html>
```

- [ ] **Step 2: 编写测试**

```python
# tests/test_reader.py
from pathlib import Path
from unittest.mock import patch
from llm_wiki.reader import read_file

FIXTURES = Path(__file__).parent / "fixtures"


class TestTextFiles:
    def test_read_markdown(self):
        content = read_file(str(FIXTURES / "sample.md"))
        assert "测试标题" in content
        assert "测试内容" in content

    def test_read_txt(self):
        content = read_file(str(FIXTURES / "sample.txt"))
        assert "纯文本测试内容" in content

    def test_read_html(self):
        content = read_file(str(FIXTURES / "sample.html"))
        assert "HTML 测试" in content
        assert "正文内容" in content
        assert "console.log" not in content  # script 标签被移除
        assert "color: red" not in content  # style 标签被移除


class TestUnsupportedFormat:
    def test_raises_for_unknown_extension(self):
        try:
            read_file("test.xyz")
            assert False, "应该抛出异常"
        except ValueError as e:
            assert "不支持的文件格式" in str(e)


class TestPDFReader:
    def test_read_pdf(self):
        with patch("llm_wiki.reader.pdfplumber") as mock_pdf:
            mock_page = mock_pdf.open.return_value.__enter__.return_value.pages[0]
            mock_page.extract_text.return_value = "PDF 测试内容"
            mock_pdf.open.return_value.__enter__.return_value.pages = [mock_page]

            with patch("pathlib.Path.exists", return_value=True):
                content = read_file("test.pdf")
                assert "PDF 测试内容" in content


class TestDocxReader:
    def test_read_docx(self):
        with patch("llm_wiki.reader.Document") as mock_doc:
            mock_para = mock_doc.return_value.paragraphs = [
                type("P", (), {"text": "段落一"})(),
                type("P", (), {"text": ""})(),
                type("P", (), {"text": "段落二"})(),
            ]
            with patch("pathlib.Path.exists", return_value=True):
                content = read_file("test.docx")
                assert "段落一" in content
                assert "段落二" in content


class TestImageReader:
    def test_read_image_delegates_to_llm(self):
        with patch("llm_wiki.reader.chat_with_image") as mock_chat:
            mock_chat.return_value = "图片中的文字内容"
            with patch("pathlib.Path.exists", return_value=True):
                content = read_file("test.png")
                assert content == "图片中的文字内容"
                mock_chat.assert_called_once()
```

- [ ] **Step 3: 运行测试确认失败**

```bash
uv run pytest tests/test_reader.py -v
```
Expected: ImportError

- [ ] **Step 4: 实现 reader.py**

```python
"""多格式文件读取器 — 将各种格式统一转换为纯文本。"""
from pathlib import Path


def read_file(file_path: str) -> str:
    """根据文件扩展名自动选择读取方式，返回纯文本内容。"""
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext in (".md", ".txt"):
        return path.read_text(encoding="utf-8")
    elif ext == ".pdf":
        return _read_pdf(path)
    elif ext in (".html", ".htm"):
        return _read_html(path)
    elif ext == ".docx":
        return _read_docx(path)
    elif ext in (".png", ".jpg", ".jpeg", ".gif", ".webp"):
        return _read_image(path)
    else:
        raise ValueError(f"不支持的文件格式: {ext}")


def _read_pdf(path: Path) -> str:
    import pdfplumber

    texts = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                texts.append(text)
    return "\n\n".join(texts)


def _read_html(path: Path) -> str:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    return soup.get_text("\n", strip=True)


def _read_docx(path: Path) -> str:
    from docx import Document

    doc = Document(str(path))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def _read_image(path: Path) -> str:
    from llm_wiki.llm import chat_with_image

    prompt = "请详细描述这张图片中的所有文字内容和视觉信息。请优先提取图中可见的所有文字，包括标题、标注、数据等。"
    return chat_with_image(prompt, str(path))
```

- [ ] **Step 5: 运行测试确认通过**

```bash
uv run pytest tests/test_reader.py -v
```
Expected: all tests pass

- [ ] **Step 6: 提交**

```bash
git add src/llm_wiki/reader.py tests/test_reader.py tests/fixtures/
git commit -m "feat: 添加多格式文件读取器，支持 md/txt/pdf/html/docx/image"
```

---

### Task 6: Prompt 模板

**Files:**
- Create: `src/llm_wiki/prompts/__init__.py`
- Create: `src/llm_wiki/prompts/ingest.py`
- Create: `src/llm_wiki/prompts/query.py`
- Create: `src/llm_wiki/prompts/lint.py`

- [ ] **Step 1: 实现 prompts/__init__.py**

```python
# src/llm_wiki/prompts/__init__.py (empty)
```

- [ ] **Step 2: 实现 prompts/ingest.py**

```python
"""摄入操作的中文 Prompt 模板。"""


def build_system_prompt(schema: str) -> str:
    return f"""你是一个知识库维护助手。你的任务是将新的来源文档整合到已有的 Wiki 知识库中。

## Wiki 结构约定

{schema}

## 你的任务

仔细阅读用户提供的来源文档，执行以下操作：

1. **创建来源摘要页** (`pages/source-来源名称.md`)：包含来源的标题、类型、关键要点（3-5条）、与已有知识的关联
2. **更新实体页**：如果文档中涉及已有实体，更新对应页面；如果涉及新实体，创建新页面
3. **更新概念页**：如果文档涉及已有概念，追加新信息；如果有新概念，创建新页面
4. **标注矛盾**：如果新信息与已有知识矛盾，在相关页面中用 "> [!矛盾]" 标注，并说明新旧观点的差异
5. **添加交叉引用**：确保新页面通过 `[[页面名]]` 链接到相关页面，相关页面也应回链

## 注意事项

- 维护 Wiki 的一致性和完整性
- 如果新来源没有带来实质性的新信息，可以只更新来源摘要页
- 不要重复已在其他页面中详细记录的内容，用 `[[页面名]]` 引用即可
- 保持页面简洁，每页聚焦一个主题
- 所有 `[[页面名]]` 中的页面名不带 `.md` 扩展名

## 输出格式

请严格按照以下格式输出你的操作方案：

```
## 分析摘要
简要说明这篇来源的核心内容和你的整合策略（2-3句话）。

## 文件操作
### 创建 pages/source-xxx.md
[完整的 Markdown 内容，包括标题、关键要点、关联页面]

### 更新 pages/实体名.md
[完整的更新后 Markdown 内容]

### 更新 pages/概念名.md
[完整的更新后 Markdown 内容]

### 更新 index.md
[完整的更新后 index.md 内容，将新页面加入对应分类]

## 日志条目
ingest | 来源标题 — 更新了 N 个页面
```

注意：
- 每个文件操作块必须包含完整的文件内容，不得省略或缩写
- 如果某个操作不需要（例如无需更新实体页），可以省略该块
- index.md 的更新应包含所有现有条目和新条目
"""


def build_user_prompt(source_text: str, index_content: str, file_name: str) -> str:
    index_section = index_content if index_content.strip() else "（当前 Wiki 为空，还没有任何页面）"
    return f"""## 当前 Wiki 索引

{index_section}

## 新来源文档

文件名：{file_name}

内容：
{source_text}

请按照系统提示词中的格式，输出你的整合方案。"""
```

- [ ] **Step 3: 实现 prompts/query.py**

```python
"""查询操作的中文 Prompt 模板。"""


def build_system_prompt(schema: str) -> str:
    return f"""你是一个知识库查询助手。你会收到用户的问题以及 Wiki 知识库中的相关页面内容。

## Wiki 结构约定

{schema}

## 你的任务

1. 仔细阅读提供的 Wiki 页面内容
2. 综合这些信息回答用户的问题
3. 在回答中引用相关的 Wiki 页面（使用 `[[页面名]]` 格式）
4. 如果当前 Wiki 内容不足以完整回答问题，诚实说明哪些信息缺失
5. 如果发现 Wiki 中的内容存在矛盾，指出矛盾所在并分析可能的原因

## 输出格式

```
## 回答
[你的回答内容。引用来源时使用 [[页面名]] 格式。]

## 引用来源
- [[页面1]]: 提供了哪些关键信息
- [[页面2]]: 提供了哪些关键信息

## 缺失信息（如适用）
- 哪些问题当前 Wiki 无法回答
- 建议补充哪些来源或调查方向
```
"""


def build_user_prompt(question: str, relevant_pages: list[tuple[str, str]]) -> str:
    if not relevant_pages:
        pages_section = "（当前 Wiki 为空，没有相关页面可以引用）"
    else:
        pages_text = "\n\n---\n\n".join(
            f"### [[{name.replace('.md', '')}]]\n\n{content}"
            for name, content in relevant_pages
        )
        pages_section = f"## 相关 Wiki 页面\n\n{pages_text}"

    return f"""## 用户问题

{question}

{pages_section}

请根据以上信息回答问题。如果当前 Wiki 信息不足，请诚实说明，并建议如何补充相关知识。"""
```

- [ ] **Step 4: 实现 prompts/lint.py**

```python
"""健康检查的中文 Prompt 模板。"""


def build_system_prompt(schema: str) -> str:
    return f"""你是一个 Wiki 知识库审查员。你的任务是全面检查 Wiki 的健康状况，发现潜在问题。

## Wiki 结构约定

{schema}

## 检查维度

请从以下维度逐一检查：

1. **矛盾检测**：不同页面对同一事实的陈述是否矛盾？具体指出矛盾内容和涉及的页面。
2. **过时信息**：是否有已被更新的来源推翻或修正的旧声明？根据日志中的时间线判断。
3. **孤立页面**：是否有页面没有被任何其他页面引用（入站链接为 0）？列出这些孤立页面。
4. **缺失页面**：是否有页面被 `[[引用]]` 但实际上不存在？列出缺失的页面。
5. **缺失交叉引用**：相关内容之间是否缺少链接？指出应该但尚未链接的页面对。
6. **知识空白**：有哪些重要概念、实体或主题被多次提及但缺少独立的专题页面？
7. **结构问题**：页面命名是否符合规范？index.md 分类是否准确完整？
8. **探索建议**：基于当前 Wiki 的知识空白，建议哪些问题值得进一步调查？哪些类型的来源值得寻找？

## 输出格式

```
## 诊断报告

### 矛盾（N 处）
1. **[[页面A]]** 与 **[[页面B]]** 在 xxx 上存在矛盾：
   - 页面A 的观点：xxx
   - 页面B 的观点：xxx
   - 建议：xxx

### 过时信息（N 处）
1. **[[页面A]]** 中的 xxx 声明已被 **[[页面B]]**（更新的来源）推翻或修正

### 孤立页面（N 个）
- [[页面A]]: 没有入站链接
- [[页面B]]: 没有入站链接

### 缺失页面（N 个）
- [[页面A]]: 被 [[页面X]] 引用但不存在
- [[页面B]]: 被 [[页面Y]] 引用但不存在

### 缺失交叉引用（N 处）
- **[[页面A]]** 与 **[[页面B]]** 都在讨论 xxx，但彼此没有链接

### 知识空白（N 处）
- xxx 概念/实体被多次提及但缺少独立页面
- yyy 主题在多个来源中涉及但未经系统整理

### 结构问题（N 处）
- xxx

### 建议
1. 建议调查的问题：
2. 建议寻找的来源类型：
```
"""


def build_user_prompt(
    all_pages: list[tuple[str, str]], index_content: str, log_content: str
) -> str:
    pages_text = "\n\n---\n\n".join(
        f"### [[{name.replace('.md', '')}]]\n\n{content}"
        for name, content in all_pages
    )

    log_section = log_content if log_content.strip() else "（暂无操作记录）"

    return f"""## 索引

{index_content}

## 操作日志

{log_section}

## 所有 Wiki 页面

{pages_text}

请对以上 Wiki 进行全面的健康检查。"""
```

- [ ] **Step 5: 提交**

```bash
git add src/llm_wiki/prompts/
git commit -m "feat: 添加中文 Prompt 模板（ingest/query/lint）"
```

---

### Task 7: Ingest 操作

**Files:**
- Create: `src/llm_wiki/operations/__init__.py`
- Create: `src/llm_wiki/operations/ingest.py`
- Create: `tests/test_operations_ingest.py`

- [ ] **Step 1: 实现 operations/__init__.py**

```python
# src/llm_wiki/operations/__init__.py (empty)
```

- [ ] **Step 2: 编写测试**

```python
# tests/test_operations_ingest.py
import tempfile
from pathlib import Path
from unittest.mock import patch
from llm_wiki.operations.ingest import run, _parse_operations, _extract_log_entry


class TestParseOperations:
    def test_parse_create_and_update(self):
        response = """## 分析摘要
这是一篇测试文章。

## 文件操作
### 创建 pages/source-test.md
# 测试来源

这是来源摘要。

### 更新 pages/概念.md
# 概念

更新后的概念内容。

### 更新 index.md
# 索引

## 来源
- [[source-test]]: 测试来源

## 日志条目
ingest | 测试来源 — 更新了 2 个页面
"""
        ops = _parse_operations(response)
        assert len(ops) == 3  # 2 file ops + 1 index op

        assert ops[0]["action"] == "create"
        assert ops[0]["path"] == "pages/source-test.md"
        assert "测试来源" in ops[0]["content"]

        assert ops[1]["action"] == "update"
        assert ops[1]["path"] == "pages/概念.md"
        assert "更新后的概念内容" in ops[1]["content"]

        assert ops[2]["action"] == "update_index"
        assert "## 来源" in ops[2]["content"]

    def test_extract_log_entry(self):
        response = """## 日志条目
ingest | 文章标题 — 更新了 3 个页面
"""
        entry = _extract_log_entry(response)
        assert entry == "ingest | 文章标题 — 更新了 3 个页面"


class TestIngestRun:
    def test_full_ingest_flow(self):
        with tempfile.TemporaryDirectory() as tmp:
            from llm_wiki.wiki import init_wiki, list_pages, read_index, read_log
            from llm_wiki.schema import write_default_schema

            wiki_dir = str(Path(tmp) / "wiki")
            raw_dir = str(Path(tmp) / "raw")
            init_wiki(wiki_dir, raw_dir)
            write_default_schema(wiki_dir)

            # Create a test source file
            source_path = Path(raw_dir) / "test_article.md"
            source_path.write_text("# 测试文章\n\n这是测试内容。", encoding="utf-8")

            mock_response = """## 分析摘要
测试文章的摘要。

## 文件操作
### 创建 pages/source-test_article.md
# 测试文章

## 关键要点
- 要点一
- 要点二

## 关联页面
- [[首页]]

### 更新 index.md
# 索引

## 来源
- [[source-test_article]]: 测试文章摘要

## 日志条目
ingest | 测试文章 — 更新了 1 个页面
"""
            with patch("llm_wiki.operations.ingest.chat", return_value=mock_response):
                result = run(str(source_path), wiki_dir, raw_dir)

            assert len(result["changes"]) > 0
            assert any("source-test_article" in c for c in result["changes"])

            log = read_log(wiki_dir)
            assert "测试文章" in log
```

- [ ] **Step 3: 运行测试确认失败**

```bash
uv run pytest tests/test_operations_ingest.py -v
```
Expected: ImportError

- [ ] **Step 4: 实现 operations/ingest.py**

```python
"""摄入操作 — 将来源文档整合到 Wiki 中。"""
import re
from pathlib import Path
from llm_wiki import wiki, schema, reader
from llm_wiki.llm import chat
from llm_wiki.prompts.ingest import build_system_prompt, build_user_prompt


def run(source_path: str, wiki_dir: str, raw_dir: str = "raw") -> dict:
    """执行摄入操作：读取来源 → 调用 LLM → 更新 Wiki。

    Returns:
        {"changes": [...], "summary": "..."}
    """
    source_text = reader.read_file(source_path)
    file_name = Path(source_path).name
    schema_content = schema.load_schema(wiki_dir)
    index_content = wiki.read_index(wiki_dir)

    system_prompt = build_system_prompt(schema_content)
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
    """解析 LLM 响应中的文件操作指令。

    Returns:
        [{"action": "create"|"update", "path": "...", "content": "..."},
         {"action": "update_index", "content": "..."}]
    """
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

    idx_pattern = r"### 更新 index\.md\n(.*?)(?=\n### |\n## |\Z)"
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
```

- [ ] **Step 5: 运行测试确认通过**

```bash
uv run pytest tests/test_operations_ingest.py -v
```
Expected: all tests pass

- [ ] **Step 6: 提交**

```bash
git add src/llm_wiki/operations/ tests/test_operations_ingest.py
git commit -m "feat: 添加 ingest 操作，支持来源文档整合到 Wiki"
```

---

### Task 8: Query 操作

**Files:**
- Create: `src/llm_wiki/operations/query.py`
- Create: `tests/test_operations_query.py`

- [ ] **Step 1: 编写测试**

```python
# tests/test_operations_query.py
import tempfile
from pathlib import Path
from unittest.mock import patch
from llm_wiki.operations.query import run


class TestQueryRun:
    def test_query_with_empty_wiki(self):
        with tempfile.TemporaryDirectory() as tmp:
            from llm_wiki.wiki import init_wiki
            from llm_wiki.schema import write_default_schema

            wiki_dir = str(Path(tmp) / "wiki")
            raw_dir = str(Path(tmp) / "raw")
            init_wiki(wiki_dir, raw_dir)
            write_default_schema(wiki_dir)

            mock_response = """## 回答
当前 Wiki 为空，无法回答此问题。

## 引用来源
（无）

## 缺失信息
建议先摄入相关来源文档。
"""
            with patch("llm_wiki.operations.query.chat", return_value=mock_response):
                result = run("什么是测试？", wiki_dir)
                assert "当前 Wiki 为空" in result["answer"]
                assert result["sources"] == []

    def test_query_with_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            from llm_wiki.wiki import init_wiki, write_page, write_index
            from llm_wiki.schema import write_default_schema

            wiki_dir = str(Path(tmp) / "wiki")
            raw_dir = str(Path(tmp) / "raw")
            init_wiki(wiki_dir, raw_dir)
            write_default_schema(wiki_dir)

            write_page(wiki_dir, "概念A.md", "# 概念A\n\n这是概念A的内容。")
            write_index(wiki_dir, "# 索引\n\n## 概念\n- [[概念A]]: 测试概念")

            mock_response = """## 回答
根据 Wiki 中概念A的记录，相关内容如下...

## 引用来源
- [[概念A]]: 提供了关于概念A的基本信息
"""
            with patch("llm_wiki.operations.query.chat", return_value=mock_response):
                result = run("概念A是什么？", wiki_dir)
                assert "概念A" in result["answer"]


class TestQueryRunWithSave:
    def test_save_answer_as_page(self):
        with tempfile.TemporaryDirectory() as tmp:
            from llm_wiki.wiki import init_wiki, write_page, write_index, read_page, read_index
            from llm_wiki.schema import write_default_schema

            wiki_dir = str(Path(tmp) / "wiki")
            raw_dir = str(Path(tmp) / "raw")
            init_wiki(wiki_dir, raw_dir)
            write_default_schema(wiki_dir)

            write_page(wiki_dir, "概念B.md", "# 概念B\n\n内容。")
            write_index(wiki_dir, "# 索引\n\n## 概念\n- [[概念B]]: 测试")

            mock_response = """## 回答
回答内容...

## 引用来源
- [[概念B]]: 提供了信息
"""
            with patch("llm_wiki.operations.query.chat", return_value=mock_response):
                result = run("问题？", wiki_dir, save=True)
                assert result["saved"]
                assert ".md" in result["saved"]

            # Verify the page was saved
            saved_page = result["saved"]
            content = read_page(wiki_dir, saved_page)
            assert "回答内容" in content
```

- [ ] **Step 2: 运行测试确认失败**

```bash
uv run pytest tests/test_operations_query.py -v
```
Expected: ImportError

- [ ] **Step 3: 实现 operations/query.py**

```python
"""查询操作 — 基于 Wiki 回答用户问题。"""
import re
from datetime import datetime
from llm_wiki import wiki, schema
from llm_wiki.llm import chat
from llm_wiki.prompts.query import build_system_prompt, build_user_prompt


def run(question: str, wiki_dir: str, save: bool = False) -> dict:
    """执行查询操作。

    Returns:
        {"answer": "...", "sources": [...], "saved": "page_name" | None}
    """
    schema_content = schema.load_schema(wiki_dir)
    index_content = wiki.read_index(wiki_dir)
    page_names = wiki.list_pages(wiki_dir)

    # Simple matching: find pages that match keywords in the question
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
        page_name = f"query-{safe_title}-{timestamp}.md"
        wiki.write_page(wiki_dir, page_name, response)
        wiki.append_log(wiki_dir, f"query | {question[:50]} — 回答已保存为 {page_name}")

        # Update index
        index_content = wiki.read_index(wiki_dir)
        new_entry = f"- [[{page_name.replace('.md', '')}]]: {question[:60]}\n"
        if "## 查询" not in index_content:
            index_content += "\n## 查询\n"
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
        # Simple: if any word from question appears in page name or content
        question_words = set(question)
        name_words = set(name)
        if question_words & name_words or len(page_names) <= 5:
            relevant.append((name, content))
    # Limit to avoid token overflow
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
```

- [ ] **Step 4: 运行测试确认通过**

```bash
uv run pytest tests/test_operations_query.py -v
```
Expected: all tests pass

- [ ] **Step 5: 提交**

```bash
git add src/llm_wiki/operations/query.py tests/test_operations_query.py
git commit -m "feat: 添加 query 操作，支持基于 Wiki 回答问题并可保存回答"
```

---

### Task 9: Lint 操作

**Files:**
- Create: `src/llm_wiki/operations/lint.py`
- Create: `tests/test_operations_lint.py`

- [ ] **Step 1: 编写测试**

```python
# tests/test_operations_lint.py
import tempfile
from pathlib import Path
from unittest.mock import patch
from llm_wiki.operations.lint import run


class TestLintRun:
    def test_lint_empty_wiki(self):
        with tempfile.TemporaryDirectory() as tmp:
            from llm_wiki.wiki import init_wiki
            from llm_wiki.schema import write_default_schema

            wiki_dir = str(Path(tmp) / "wiki")
            raw_dir = str(Path(tmp) / "raw")
            init_wiki(wiki_dir, raw_dir)
            write_default_schema(wiki_dir)

            mock_response = """## 诊断报告

### 矛盾（0 处）
无。

### 过时信息（0 处）
无。

### 孤立页面（0 个）
无。

### 缺失页面（0 个）
无。

### 缺失交叉引用（0 处）
无。

### 知识空白（1 处）
- Wiki 为空，建议开始摄入来源文档

### 建议
1. 建议开始摄入第一批来源文档
"""
            with patch("llm_wiki.operations.lint.chat", return_value=mock_response):
                result = run(wiki_dir)
                assert "诊断报告" in result
                assert "知识空白" in result

    def test_lint_with_pages(self):
        with tempfile.TemporaryDirectory() as tmp:
            from llm_wiki.wiki import init_wiki, write_page, write_index, append_log
            from llm_wiki.schema import write_default_schema

            wiki_dir = str(Path(tmp) / "wiki")
            raw_dir = str(Path(tmp) / "raw")
            init_wiki(wiki_dir, raw_dir)
            write_default_schema(wiki_dir)

            write_page(wiki_dir, "page1.md", "# 页面1\n\n内容。\n\n## 相关\n- [[page2]]")
            write_page(wiki_dir, "page2.md", "# 页面2\n\n内容。")
            write_index(wiki_dir, "# 索引\n- [[page1]]")
            append_log(wiki_dir, "ingest | 测试来源")

            mock_response = """## 诊断报告

### 缺失页面（1 个）
- [[page2]]: 被 [[page1]] 引用但不存在

### 建议
无。
"""
            # Note: page2 exists but the LLM might flag it as missing
            # This test verifies the flow, not the LLM's judgment
            with patch("llm_wiki.operations.lint.chat", return_value=mock_response):
                result = run(wiki_dir)
                assert "诊断报告" in result or "缺失" in result
```

- [ ] **Step 2: 运行测试确认失败**

```bash
uv run pytest tests/test_operations_lint.py -v
```
Expected: ImportError

- [ ] **Step 3: 实现 operations/lint.py**

```python
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
```

- [ ] **Step 4: 运行测试确认通过**

```bash
uv run pytest tests/test_operations_lint.py -v
```
Expected: all tests pass

- [ ] **Step 5: 提交**

```bash
git add src/llm_wiki/operations/lint.py tests/test_operations_lint.py
git commit -m "feat: 添加 lint 操作，支持 Wiki 健康检查"
```

---

### Task 10: CLI 入口

**Files:**
- Create: `src/llm_wiki/cli.py`

- [ ] **Step 1: 实现 cli.py**

```python
"""CLI 入口 — 提供 init/ingest/query/lint/chat 命令。"""
import os
import sys
import click
from pathlib import Path


def _get_dirs():
    """获取 wiki_dir 和 raw_dir，优先使用环境变量。"""
    wiki_dir = os.getenv("LLM_WIKI_DIR", str(Path.cwd() / "wiki"))
    raw_dir = os.getenv("LLM_RAW_DIR", str(Path.cwd() / "raw"))
    return wiki_dir, raw_dir


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
    wiki_dir = wiki_dir or os.getenv("LLM_WIKI_DIR", str(Path.cwd() / "wiki"))
    raw_dir = raw_dir or os.getenv("LLM_RAW_DIR", str(Path.cwd() / "raw"))

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

        # Default: query the wiki
        click.echo()
        try:
            response = llm_chat(system_prompt, user_input)
            click.echo(response)
        except Exception as e:
            click.echo(f"错误：{e}")
        click.echo()


def _get_wiki_raw_dirs(wiki_dir, raw_dir=None):
    """获取 wiki_dir 和 raw_dir。"""
    wiki = wiki_dir or os.getenv("LLM_WIKI_DIR", str(Path.cwd() / "wiki"))
    raw = raw_dir or os.getenv("LLM_RAW_DIR", str(Path.cwd() / "raw"))
    return wiki, raw


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 验证 CLI 可正常启动**

```bash
uv run llm-wiki --help
```
Expected: 显示帮助信息

- [ ] **Step 3: 验证 init 命令**

```bash
uv run llm-wiki init --wiki-dir /tmp/test-wiki --raw-dir /tmp/test-raw
```
Expected: 成功初始化，显示目录结构

- [ ] **Step 4: 提交**

```bash
git add src/llm_wiki/cli.py
git commit -m "feat: 添加 CLI 入口，支持 init/ingest/query/lint/chat 命令"
```

---

### Task 11: 集成验证与最终检查

- [ ] **Step 1: 运行全部测试**

```bash
uv run pytest tests/ -v
```
Expected: 所有测试通过

- [ ] **Step 2: 验证 CLI 帮助信息**

```bash
uv run llm-wiki --help
uv run llm-wiki init --help
uv run llm-wiki ingest --help
uv run llm-wiki query --help
uv run llm-wiki lint --help
```
Expected: 每个命令都显示正确的帮助信息（中文）

- [ ] **Step 3: 检查代码质量**

```bash
uv run ruff check src/ tests/
```
Expected: 无错误或仅有可忽略的警告

- [ ] **Step 4: 最终提交**

```bash
git add -A
git commit -m "chore: 集成验证，确保所有测试通过"
```
