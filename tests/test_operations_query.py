"""测试查询操作 — 基于 index 检索。"""

from unittest.mock import patch
from tests.conftest import make_mock_client


class TestQueryRun:
    def test_query_with_empty_wiki(self):
        client = make_mock_client()

        mock_response = """## 回答
当前 Wiki 为空，无法回答此问题。

## 引用来源
（无）

## 缺失信息
建议先摄入相关来源文档。
"""
        with (
            patch("siyuan_llm_wiki.operations.query.chat", return_value=mock_response),
            patch("siyuan_llm_wiki.wiki.get_client", return_value=client),
            patch("siyuan_llm_wiki.schema.load_schema", return_value="# Schema"),
        ):
            from siyuan_llm_wiki.operations.query import run

            result = run("什么是测试？")
            assert "当前 Wiki 为空" in result["answer"]
            assert result["sources"] == []

    def test_query_with_content(self):
        client = make_mock_client()

        # 设置 index 包含 [[概念A]] 条目
        from siyuan_llm_wiki.wiki import write_index, write_page

        with patch("siyuan_llm_wiki.wiki.get_client", return_value=client):
            write_page("concepts/概念A", "# 概念A\n\n这是概念A的详细内容。")
            write_index("""# 索引

## 概念
- [[概念A]]: 一个测试概念
""")

        chat_retrieval = "concepts/概念A"
        chat_answer = """## 回答
根据 Wiki 中概念A的记录，相关内容如下...

## 引用来源
- [[概念A]]: 提供了关于概念A的基本信息
"""
        with (
            patch(
                "siyuan_llm_wiki.operations.query.chat",
                side_effect=[chat_retrieval, chat_answer],
            ),
            patch("siyuan_llm_wiki.wiki.get_client", return_value=client),
            patch("siyuan_llm_wiki.schema.load_schema", return_value="# Schema"),
        ):
            from siyuan_llm_wiki.operations.query import run

            result = run("概念A是什么？")
            assert "概念A" in result["answer"]


class TestQueryRunWithSave:
    def test_save_answer_as_page(self):
        client = make_mock_client()

        chat_retrieval = "concepts/概念B"
        chat_answer = """## 回答
回答内容...

## 引用来源
- [[概念B]]: 提供了信息
"""
        with (
            patch(
                "siyuan_llm_wiki.operations.query.chat",
                side_effect=[chat_retrieval, chat_answer],
            ),
            patch(
                "siyuan_llm_wiki.operations.ingest.run_text",
                return_value={"changes": ["sources/source-query-xxx"], "summary": "ok"},
            ),
            patch("siyuan_llm_wiki.wiki.get_client", return_value=client),
            patch("siyuan_llm_wiki.schema.load_schema", return_value="# Schema"),
        ):
            from siyuan_llm_wiki.operations.query import run

            result = run("问题？", save=True)
            assert result["saved"]
            assert "source" in result["saved"] or "query" in result["saved"]
