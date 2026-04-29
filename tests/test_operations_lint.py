"""测试健康检查操作。"""

from unittest.mock import patch
from tests.conftest import make_mock_client


class TestLintRun:
    def test_lint_empty_wiki(self):
        client = make_mock_client()

        mock_response = """## 诊断报告

### 矛盾（0 处）
无。

### 知识空白（1 处）
- Wiki 为空，建议开始摄入来源文档

### 建议
1. 建议开始摄入第一批来源文档
"""
        with (
            patch("siyuan_llm_wiki.operations.lint.chat", return_value=mock_response),
            patch("siyuan_llm_wiki.wiki.get_client", return_value=client),
            patch("siyuan_llm_wiki.schema.load_schema", return_value="# Schema"),
        ):
            from siyuan_llm_wiki.operations.lint import run

            result = run()
            assert "诊断报告" in result
            assert "知识空白" in result

    def test_lint_with_pages(self):
        client = make_mock_client()

        mock_response = """## 诊断报告

### 缺失页面（1 个）
- [[page2]]: 被 [[page1]] 引用但不存在

### 建议
无。
"""
        with (
            patch("siyuan_llm_wiki.operations.lint.chat", return_value=mock_response),
            patch("siyuan_llm_wiki.wiki.get_client", return_value=client),
            patch("siyuan_llm_wiki.schema.load_schema", return_value="# Schema"),
        ):
            from siyuan_llm_wiki.operations.lint import run

            result = run()
            assert "诊断报告" in result or "缺失" in result
