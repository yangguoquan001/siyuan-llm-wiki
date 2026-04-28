"""测试健康检查操作。"""

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


class TestLintRun:
    def test_lint_empty_wiki(self):
        client = _make_mock_client()

        mock_response = """## 诊断报告

### 矛盾（0 处）
无。

### 知识空白（1 处）
- Wiki 为空，建议开始摄入来源文档

### 建议
1. 建议开始摄入第一批来源文档
"""
        with (
            patch("llm_wiki.operations.lint.chat", return_value=mock_response),
            patch("llm_wiki.wiki.get_client", return_value=client),
            patch("llm_wiki.schema.load_schema", return_value="# Schema"),
        ):
            from llm_wiki.operations.lint import run

            result = run()
            assert "诊断报告" in result
            assert "知识空白" in result

    def test_lint_with_pages(self):
        client = _make_mock_client()

        mock_response = """## 诊断报告

### 缺失页面（1 个）
- [[page2]]: 被 [[page1]] 引用但不存在

### 建议
无。
"""
        with (
            patch("llm_wiki.operations.lint.chat", return_value=mock_response),
            patch("llm_wiki.wiki.get_client", return_value=client),
            patch("llm_wiki.schema.load_schema", return_value="# Schema"),
        ):
            from llm_wiki.operations.lint import run

            result = run()
            assert "诊断报告" in result or "缺失" in result
