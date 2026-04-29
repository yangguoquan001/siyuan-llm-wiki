"""测试 schema.py — 使用模拟的思源 API。"""

from unittest.mock import patch, MagicMock
from siyuan_llm_wiki.schema import DEFAULT_SCHEMA


def test_default_schema_is_chinese():
    assert "Wiki 结构约定" in DEFAULT_SCHEMA
    assert "页面类型" in DEFAULT_SCHEMA
    assert "来源摘要页" in DEFAULT_SCHEMA
    assert "交叉引用" in DEFAULT_SCHEMA


def test_load_schema_returns_default_when_no_file():
    """当 /schema 文档为空时返回默认 schema。"""
    mock_client = MagicMock()
    mock_client.get_ids_by_hpath.return_value = []
    mock_client.export_md_content.return_value = ""

    with patch("siyuan_llm_wiki.wiki.get_client", return_value=mock_client):
        from siyuan_llm_wiki.schema import load_schema

        result = load_schema()
        assert result == DEFAULT_SCHEMA


def test_load_schema_returns_doc_content():
    """当 /schema 有内容时返回文档内容。"""
    mock_client = MagicMock()
    mock_client.get_ids_by_hpath.return_value = ["20250101000000-abc123"]
    mock_client.export_md_content.return_value = "# 自定义 Schema"

    with patch("siyuan_llm_wiki.wiki.get_client", return_value=mock_client):
        from siyuan_llm_wiki.schema import load_schema

        result = load_schema()
        assert result == "# 自定义 Schema"


def test_write_default_schema_writes_when_empty():
    """当 /schema 为空时写入默认 schema。"""
    mock_client = MagicMock()
    mock_client.get_ids_by_hpath.return_value = ["20250101000000-abc123"]
    mock_client.export_md_content.return_value = ""

    with (
        patch("siyuan_llm_wiki.wiki.get_client", return_value=mock_client),
        patch("siyuan_llm_wiki.siyuan.get_client", return_value=mock_client),
    ):
        from siyuan_llm_wiki.schema import write_default_schema

        write_default_schema()
        # delete_block + create_doc 应该被调用
        mock_client.delete_block.assert_called_once()
        mock_client.create_doc.assert_called_once()


def test_write_default_schema_does_not_overwrite():
    """当 /schema 已有内容时不覆盖。"""
    mock_client = MagicMock()
    mock_client.get_ids_by_hpath.return_value = ["20250101000000-abc123"]
    mock_client.export_md_content.return_value = "# 我的自定义 Schema"

    with patch("siyuan_llm_wiki.wiki.get_client", return_value=mock_client):
        from siyuan_llm_wiki.schema import write_default_schema

        write_default_schema()
        mock_client.update_block.assert_not_called()
        mock_client.create_doc.assert_not_called()


def test_load_schema_returns_default_when_empty_string():
    """当 /schema 内容为空字符串时返回默认。"""
    mock_client = MagicMock()
    mock_client.get_ids_by_hpath.return_value = ["20250101000000-abc123"]
    mock_client.export_md_content.return_value = "   "  # 空白

    with patch("siyuan_llm_wiki.wiki.get_client", return_value=mock_client):
        from siyuan_llm_wiki.schema import load_schema

        result = load_schema()
        assert result == DEFAULT_SCHEMA
