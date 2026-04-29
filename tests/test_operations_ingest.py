"""测试摄入操作 — 解析 + 端到端流程。"""

from unittest.mock import patch, MagicMock
from siyuan_llm_wiki.operations.ingest import _parse_operations, _extract_log_entry


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
    def _make_mock_client(self):
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
                    real_path = key[6:]
                    docs[real_path] = markdown
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

    def test_full_ingest_flow(self):
        client = self._make_mock_client()

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
