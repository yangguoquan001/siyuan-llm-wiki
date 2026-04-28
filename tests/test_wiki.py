"""测试 wiki.py — 通过模拟思源 API 验证 wiki 操作。"""

from unittest.mock import patch, MagicMock
from llm_wiki.wiki import (
    init_wiki,
    read_page,
    write_page,
    read_index,
    write_index,
    append_log,
    read_log,
    list_pages,
    get_page_id,
    get_all_page_ids,
)


def _make_mock_client():
    """创建模拟 SiYuan 客户端，维护内存中的文档存储。"""
    client = MagicMock()
    docs: dict[str, str] = {}  # {hpath: content}
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
        for path, stored_id in list(docs.items()):
            if stored_id == block_id and path.startswith("__id__"):
                real_path = path[6:]  # strip __id__ prefix
                docs[real_path] = markdown
                break

    def _export_md_content(block_id):
        for path, stored_id in list(docs.items()):
            if stored_id == block_id and path.startswith("__id__"):
                real_path = path[6:]
                return docs.get(real_path, "")
        # Also check if block_id is a path directly
        for path in docs:
            if not path.startswith("__id__") and docs.get(f"__id__{path}") == block_id:
                return docs.get(path, "")
        return ""

    def _sql_query(stmt):
        # 模拟 SQL 查询返回页面列表
        if "LIKE '/pages/%'" in stmt:
            results = []
            for path, content in docs.items():
                if path.startswith("/pages/") and not path.startswith("__id__"):
                    bid = docs.get(f"__id__{path}", "")
                    results.append({"id": bid, "hpath": path})
            return results
        return []

    client.get_ids_by_hpath.side_effect = _get_ids_by_hpath
    client.create_doc.side_effect = _create_doc
    client.update_block.side_effect = _update_block
    client.export_md_content.side_effect = _export_md_content
    client.sql_query.side_effect = _sql_query
    client.get_child_blocks.return_value = []

    return client


class TestInitWiki:
    def test_init_creates_root_docs(self):
        client = _make_mock_client()
        with patch("llm_wiki.wiki.get_client", return_value=client):
            with patch("pathlib.Path.mkdir"):
                init_wiki("raw")
            # 应创建了 /schema, /index, /log
            assert client.create_doc.call_count >= 3


class TestPageOperations:
    def test_write_and_read_page(self):
        client = _make_mock_client()
        with patch("llm_wiki.wiki.get_client", return_value=client):
            bid = write_page("test-page", "# 测试页面\n内容")
            assert bid
            content = read_page("test-page")
            assert content == "# 测试页面\n内容"

    def test_write_page_subdirectory(self):
        client = _make_mock_client()
        with patch("llm_wiki.wiki.get_client", return_value=client):
            bid = write_page("sub/dir/test", "# 子目录测试")
            assert bid
            content = read_page("sub/dir/test")
            assert content == "# 子目录测试"

    def test_read_nonexistent_page_returns_empty(self):
        client = _make_mock_client()
        with patch("llm_wiki.wiki.get_client", return_value=client):
            assert read_page("nonexistent") == ""

    def test_write_existing_page_updates(self):
        client = _make_mock_client()
        with patch("llm_wiki.wiki.get_client", return_value=client):
            write_page("test", "# V1")
            bid2 = write_page("test", "# V2")
            assert bid2
            content = read_page("test")
            assert content == "# V2"


class TestIndexOperations:
    def test_write_and_read_index(self):
        client = _make_mock_client()
        with patch("llm_wiki.wiki.get_client", return_value=client):
            write_index("# 索引\n- [[page1]]")
            content = read_index()
            assert content == "# 索引\n- [[page1]]"


class TestLogOperations:
    def test_append_and_read_log(self):
        client = _make_mock_client()
        with patch("llm_wiki.wiki.get_client", return_value=client):
            append_log("ingest | 测试文档")
            log = read_log()
            assert "ingest | 测试文档" in log

    def test_multiple_entries(self):
        client = _make_mock_client()
        with patch("llm_wiki.wiki.get_client", return_value=client):
            append_log("ingest | 文档A")
            append_log("query | 问题B")
            log = read_log()
            assert "文档A" in log
            assert "问题B" in log


class TestListPages:
    def test_list_pages_empty(self):
        client = _make_mock_client()
        with patch("llm_wiki.wiki.get_client", return_value=client):
            pages = list_pages()
            assert pages == []


class TestGetPageId:
    def test_get_page_id(self):
        client = _make_mock_client()
        with patch("llm_wiki.wiki.get_client", return_value=client):
            bid = write_page("entities/test-entity", "# Entity")
            found = get_page_id("entities/test-entity")
            assert found == bid

    def test_get_page_id_nonexistent(self):
        client = _make_mock_client()
        with patch("llm_wiki.wiki.get_client", return_value=client):
            assert get_page_id("nonexistent") == ""


class TestGetAllPageIds:
    def test_get_all_page_ids(self):
        client = _make_mock_client()
        with patch("llm_wiki.wiki.get_client", return_value=client):
            write_page("sources/src1", "# Source 1")
            write_page("entities/ent1", "# Entity 1")
            mapping = get_all_page_ids()
            assert "sources/src1" in mapping
            assert "entities/ent1" in mapping
