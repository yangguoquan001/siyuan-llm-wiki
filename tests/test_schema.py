import tempfile
from pathlib import Path
from llm_wiki.schema import load_schema, write_default_schema, DEFAULT_SCHEMA


def test_default_schema_is_chinese():
    assert "Wiki 结构约定" in DEFAULT_SCHEMA
    assert "页面类型" in DEFAULT_SCHEMA
    assert "来源摘要页" in DEFAULT_SCHEMA
    assert "交叉引用" in DEFAULT_SCHEMA


def test_load_schema_returns_default_when_no_file():
    with tempfile.TemporaryDirectory() as tmp:
        result = load_schema(tmp)
        assert result == DEFAULT_SCHEMA


def test_load_schema_returns_file_content():
    with tempfile.TemporaryDirectory() as tmp:
        schema_path = Path(tmp) / "schema.md"
        schema_path.write_text("# 自定义 Schema", encoding="utf-8")
        result = load_schema(tmp)
        assert result == "# 自定义 Schema"


def test_write_default_schema_creates_file():
    with tempfile.TemporaryDirectory() as tmp:
        write_default_schema(tmp)
        schema_path = Path(tmp) / "schema.md"
        assert schema_path.exists()
        content = schema_path.read_text(encoding="utf-8")
        assert "Wiki 结构约定" in content


def test_write_default_schema_does_not_overwrite():
    with tempfile.TemporaryDirectory() as tmp:
        schema_path = Path(tmp) / "schema.md"
        schema_path.write_text("# 我的自定义 Schema", encoding="utf-8")
        write_default_schema(tmp)
        assert schema_path.read_text(encoding="utf-8") == "# 我的自定义 Schema"
