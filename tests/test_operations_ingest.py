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
ingest | 测试来源 \u2014 更新了 2 个页面
"""
        ops = _parse_operations(response)
        assert len(ops) == 3

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
ingest | 文章标题 \u2014 更新了 3 个页面
"""
        entry = _extract_log_entry(response)
        assert entry == "ingest | 文章标题 \u2014 更新了 3 个页面"


class TestIngestRun:
    def test_full_ingest_flow(self):
        with tempfile.TemporaryDirectory() as tmp:
            from llm_wiki.wiki import init_wiki, list_pages, read_index, read_log
            from llm_wiki.schema import write_default_schema

            wiki_dir = str(Path(tmp) / "wiki")
            raw_dir = str(Path(tmp) / "raw")
            init_wiki(wiki_dir, raw_dir)
            write_default_schema(wiki_dir)

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
ingest | 测试文章 \u2014 更新了 1 个页面
"""
            with patch("llm_wiki.operations.ingest.chat", return_value=mock_response):
                result = run(str(source_path), wiki_dir, raw_dir)

            assert len(result["changes"]) > 0
            assert any("source-test_article" in c for c in result["changes"])
            log = read_log(wiki_dir)
            assert "测试文章" in log
