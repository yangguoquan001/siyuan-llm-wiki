"""测试摄入操作 — 解析 + 端到端流程。"""

from unittest.mock import patch
from siyuan_llm_wiki.operations.ingest import _parse_operations, _extract_log_entry
from tests.conftest import make_mock_client


class TestParseOperations:
    def test_parse_create_and_update(self):
        """解析创建和更新操作（新格式：无 pages/ 前缀，无 .md 扩展名）。"""
        response = """## 分析摘要
这是一篇测试文章。

## 文件操作
### 创建 sources/source-test
# 测试来源

这是来源摘要。

### 更新 concepts/概念
# 概念

更新后的概念内容。

### 更新 index
# 索引

## 来源
- [[source-test]]: 测试来源

## 日志条目
ingest | 测试来源 — 更新了 2 个页面
"""
        ops = _parse_operations(response)
        assert len(ops) == 3

        assert ops[0]["action"] == "create"
        assert ops[0]["path"] == "sources/source-test"
        assert "测试来源" in ops[0]["content"]

        assert ops[1]["action"] == "update"
        assert ops[1]["path"] == "concepts/概念"
        assert "更新后的概念内容" in ops[1]["content"]

        assert ops[2]["action"] == "update_index"
        assert "## 来源" in ops[2]["content"]

    def test_extract_log_entry(self):
        response = """## 日志条目
ingest | 文章标题 — 更新了 3 个页面
"""
        entry = _extract_log_entry(response)
        assert entry == "ingest | 文章标题 — 更新了 3 个页面"

    def test_parse_page_with_internal_headers(self):
        """页面内容包含 ## 分段时不会在分段处被截断。"""
        response = """## 分析摘要
测试。

## 文件操作
### 创建 sources/source-test
# 测试来源

## 基本信息
- **类型**: 论文

## 关键要点
### 要点一
详细的描述内容。

### 更新 entities/实体
# 实体

## 详细描述
这是一个详细的描述段落。

## 日志条目
ingest | 测试 — 完成
"""
        ops = _parse_operations(response)
        assert len(ops) == 2
        assert "## 基本信息" in ops[0]["content"]
        assert "## 关键要点" in ops[0]["content"]
        assert "要点一" in ops[0]["content"]
        assert "## 详细描述" in ops[1]["content"]

    def test_parse_create_index(self):
        """首次摄入时 LLM 可能输出 创建 index。"""
        response = """## 文件操作
### 创建 index
# 索引

## 来源
- [[source-x]]: 测试来源

## 日志条目
ingest | 测试
"""
        ops = _parse_operations(response)
        assert len(ops) == 1
        assert ops[0]["action"] == "update_index"
        assert "## 来源" in ops[0]["content"]


class TestIngestRun:
    def test_full_ingest_flow(self):
        client = make_mock_client()

        mock_response = """## 分析摘要
测试文章的摘要。

## 文件操作
### 创建 sources/source-test_article
# 测试文章

## 关键要点
- 要点一
- 要点二

## 关联页面
- [[首页]]

### 更新 index
# 索引

## 来源
- [[source-test_article]]: 测试文章摘要

## 日志条目
ingest | 测试文章 — 更新了 1 个页面
"""
        with (
            patch("siyuan_llm_wiki.operations.ingest.chat", return_value=mock_response),
            patch("siyuan_llm_wiki.wiki.get_client", return_value=client),
            patch("siyuan_llm_wiki.siyuan.get_client", return_value=client),
            patch("siyuan_llm_wiki.schema.load_schema", return_value="# Schema"),
            patch(
                "siyuan_llm_wiki.operations.ingest.reader.read_file", return_value="# 测试内容"
            ),
        ):
            from siyuan_llm_wiki.operations.ingest import run

            result = run("test.md")

        assert len(result["changes"]) > 0
        assert any("source-test_article" in c for c in result["changes"])
        assert "index" in result["changes"]
