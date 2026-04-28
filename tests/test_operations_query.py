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
            from llm_wiki.wiki import init_wiki, write_page, write_index, read_page
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

            saved_page = result["saved"]
            content = read_page(wiki_dir, saved_page)
            assert "回答内容" in content
