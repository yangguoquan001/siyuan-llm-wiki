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

            write_page(
                wiki_dir, "page1.md", "# 页面1\n\n内容。\n\n## 相关\n- [[page2]]"
            )
            write_page(wiki_dir, "page2.md", "# 页面2\n\n内容。")
            write_index(wiki_dir, "# 索引\n- [[page1]]")
            append_log(wiki_dir, "ingest | 测试来源")

            mock_response = """## 诊断报告

### 缺失页面（1 个）
- [[page2]]: 被 [[page1]] 引用但不存在

### 建议
无。
"""
            with patch("llm_wiki.operations.lint.chat", return_value=mock_response):
                result = run(wiki_dir)
                assert "诊断报告" in result or "缺失" in result
