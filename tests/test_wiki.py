"""测试 wiki.py — 通过模拟思源 API 验证 wiki 操作。"""

from unittest.mock import patch
from siyuan_llm_wiki.wiki import (
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
from tests.conftest import make_mock_client


class TestInitWiki:
    def test_init_creates_root_docs(self):
        client = make_mock_client()
        with patch("siyuan_llm_wiki.wiki.get_client", return_value=client):
            with patch("pathlib.Path.mkdir"):
                init_wiki("raw")
            # 应创建 /index, /log（/schema 由 write_default_schema 负责）
            assert client.create_doc.call_count >= 2


class TestPageOperations:
    def test_write_and_read_page(self):
        client = make_mock_client()
        with patch("siyuan_llm_wiki.wiki.get_client", return_value=client):
            bid = write_page("test-page", "# 测试页面\n内容")
            assert bid
            content = read_page("test-page")
            assert content == "# 测试页面\n内容"

    def test_write_page_subdirectory(self):
        client = make_mock_client()
        with patch("siyuan_llm_wiki.wiki.get_client", return_value=client):
            bid = write_page("sub/dir/test", "# 子目录测试")
            assert bid
            content = read_page("sub/dir/test")
            assert content == "# 子目录测试"

    def test_read_nonexistent_page_returns_empty(self):
        client = make_mock_client()
        with patch("siyuan_llm_wiki.wiki.get_client", return_value=client):
            assert read_page("nonexistent") == ""

    def test_write_existing_page_updates(self):
        client = make_mock_client()
        with patch("siyuan_llm_wiki.wiki.get_client", return_value=client):
            write_page("test", "# V1")
            bid2 = write_page("test", "# V2")
            assert bid2
            content = read_page("test")
            assert content == "# V2"


class TestIndexOperations:
    def test_write_and_read_index(self):
        client = make_mock_client()
        with patch("siyuan_llm_wiki.wiki.get_client", return_value=client):
            write_index("# 索引\n- [[page1]]")
            content = read_index()
            assert content == "# 索引\n- [[page1]]"


class TestLogOperations:
    def test_append_and_read_log(self):
        client = make_mock_client()
        with patch("siyuan_llm_wiki.wiki.get_client", return_value=client):
            append_log("ingest | 测试文档")
            log = read_log()
            assert "ingest | 测试文档" in log

    def test_multiple_entries(self):
        client = make_mock_client()
        with patch("siyuan_llm_wiki.wiki.get_client", return_value=client):
            append_log("ingest | 文档A")
            append_log("query | 问题B")
            log = read_log()
            assert "文档A" in log
            assert "问题B" in log


class TestListPages:
    def test_list_pages_empty(self):
        client = make_mock_client()
        with patch("siyuan_llm_wiki.wiki.get_client", return_value=client):
            pages = list_pages()
            assert pages == []


class TestGetPageId:
    def test_get_page_id(self):
        client = make_mock_client()
        with patch("siyuan_llm_wiki.wiki.get_client", return_value=client):
            bid = write_page("entities/test-entity", "# Entity")
            found = get_page_id("entities/test-entity")
            assert found == bid

    def test_get_page_id_nonexistent(self):
        client = make_mock_client()
        with patch("siyuan_llm_wiki.wiki.get_client", return_value=client):
            assert get_page_id("nonexistent") == ""


class TestGetAllPageIds:
    def test_get_all_page_ids(self):
        client = make_mock_client()
        with patch("siyuan_llm_wiki.wiki.get_client", return_value=client):
            write_page("sources/src1", "# Source 1")
            write_page("entities/ent1", "# Entity 1")
            mapping = get_all_page_ids()
            assert "sources/src1" in mapping
            assert "entities/ent1" in mapping
