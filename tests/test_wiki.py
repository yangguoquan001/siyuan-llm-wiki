import tempfile
from pathlib import Path
from llm_wiki.wiki import (
    init_wiki,
    read_page,
    write_page,
    read_index,
    write_index,
    append_log,
    read_log,
    list_pages,
)


class TestInitWiki:
    def test_creates_directories_and_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            wiki_dir = str(Path(tmp) / "wiki")
            raw_dir = str(Path(tmp) / "raw")
            init_wiki(wiki_dir, raw_dir)
            assert Path(wiki_dir).is_dir()
            assert (Path(wiki_dir) / "pages").is_dir()
            assert (Path(wiki_dir) / "schema.md").exists()
            assert (Path(wiki_dir) / "index.md").exists()
            assert (Path(wiki_dir) / "log.md").exists()
            assert Path(raw_dir).is_dir()

    def test_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            wiki_dir = str(Path(tmp) / "wiki")
            raw_dir = str(Path(tmp) / "raw")
            init_wiki(wiki_dir, raw_dir)
            init_wiki(wiki_dir, raw_dir)
            assert Path(wiki_dir).is_dir()


class TestPageOperations:
    def test_write_and_read_page(self):
        with tempfile.TemporaryDirectory() as tmp:
            wiki_dir = str(Path(tmp) / "wiki")
            init_wiki(wiki_dir, str(Path(tmp) / "raw"))
            write_page(wiki_dir, "test.md", "# 测试页面\n内容")
            content = read_page(wiki_dir, "test.md")
            assert content == "# 测试页面\n内容"

    def test_write_page_subdirectory(self):
        with tempfile.TemporaryDirectory() as tmp:
            wiki_dir = str(Path(tmp) / "wiki")
            init_wiki(wiki_dir, str(Path(tmp) / "raw"))
            write_page(wiki_dir, "sub/dir/test.md", "# 子目录测试")
            content = read_page(wiki_dir, "sub/dir/test.md")
            assert content == "# 子目录测试"

    def test_read_nonexistent_page_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            wiki_dir = str(Path(tmp) / "wiki")
            init_wiki(wiki_dir, str(Path(tmp) / "raw"))
            assert read_page(wiki_dir, "nonexistent.md") == ""


class TestIndexOperations:
    def test_write_and_read_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            wiki_dir = str(Path(tmp) / "wiki")
            init_wiki(wiki_dir, str(Path(tmp) / "raw"))
            write_index(wiki_dir, "# 索引\n- [[page1]]")
            assert read_index(wiki_dir) == "# 索引\n- [[page1]]"


class TestLogOperations:
    def test_append_and_read_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            wiki_dir = str(Path(tmp) / "wiki")
            init_wiki(wiki_dir, str(Path(tmp) / "raw"))
            append_log(wiki_dir, "ingest | 测试文档")
            log = read_log(wiki_dir)
            assert "ingest | 测试文档" in log

    def test_multiple_entries(self):
        with tempfile.TemporaryDirectory() as tmp:
            wiki_dir = str(Path(tmp) / "wiki")
            init_wiki(wiki_dir, str(Path(tmp) / "raw"))
            append_log(wiki_dir, "ingest | 文档A")
            append_log(wiki_dir, "query | 问题B")
            log = read_log(wiki_dir)
            assert "文档A" in log
            assert "问题B" in log


class TestListPages:
    def test_list_pages(self):
        with tempfile.TemporaryDirectory() as tmp:
            wiki_dir = str(Path(tmp) / "wiki")
            init_wiki(wiki_dir, str(Path(tmp) / "raw"))
            write_page(wiki_dir, "a.md", "# A")
            write_page(wiki_dir, "sub/b.md", "# B")
            pages = list_pages(wiki_dir)
            assert set(pages) == {"a.md", "sub/b.md"}

    def test_list_pages_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            wiki_dir = str(Path(tmp) / "wiki")
            init_wiki(wiki_dir, str(Path(tmp) / "raw"))
            assert list_pages(wiki_dir) == []
