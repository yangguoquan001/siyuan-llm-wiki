"""测试查询操作 — 基于 index 检索。"""

from unittest.mock import patch, MagicMock


def _make_mock_client():
    """创建带内存存储的模拟 SiYuan 客户端。"""
    client = MagicMock()
    docs: dict[str, str] = {}
    id_counter = [0]

    def _next_id():
        id_counter[0] += 1
        return f"20250101000000-test{id_counter[0]:04d}"

    def _get_ids_by_hpath(path):
        if path in docs:
            return [docs.get(f"__id__{path}", "")]
        return []

    def _create_doc(path, markdown):
        bid = _next_id()
        docs[path] = markdown
        docs[f"__id__{path}"] = bid
        return bid

    def _update_block(block_id, markdown):
        for key, val in list(docs.items()):
            if val == block_id and key.startswith("__id__"):
                docs[key[6:]] = markdown
                break

    def _export_md_content(block_id):
        for key, val in list(docs.items()):
            if val == block_id and key.startswith("__id__"):
                return docs.get(key[6:], "")
        return ""

    def _sql_query(stmt):
        results = []
        for path in docs:
            if path.startswith("/pages/") and not path.startswith("__id__"):
                bid = docs.get(f"__id__{path}", "")
                results.append({"id": bid, "hpath": path})
        return results

    client.get_ids_by_hpath.side_effect = _get_ids_by_hpath
    client.create_doc.side_effect = _create_doc
    client.update_block.side_effect = _update_block
    client.export_md_content.side_effect = _export_md_content
    client.sql_query.side_effect = _sql_query
    client.get_child_blocks.return_value = []

    return client


class TestQueryRun:
    def test_query_with_empty_wiki(self):
        client = _make_mock_client()

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
        client = _make_mock_client()

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
        client = _make_mock_client()

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
