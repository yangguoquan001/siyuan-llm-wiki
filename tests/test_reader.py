from pathlib import Path
from unittest.mock import patch, MagicMock
from llm_wiki.reader import read_file

FIXTURES = Path(__file__).parent / "fixtures"


class TestTextFiles:
    def test_read_markdown(self):
        content = read_file(str(FIXTURES / "sample.md"))
        assert "测试标题" in content
        assert "测试内容" in content

    def test_read_txt(self):
        content = read_file(str(FIXTURES / "sample.txt"))
        assert "纯文本测试内容" in content

    def test_read_html(self):
        content = read_file(str(FIXTURES / "sample.html"))
        assert "HTML 测试" in content
        assert "正文内容" in content
        assert "console.log" not in content
        assert "color: red" not in content


class TestUnsupportedFormat:
    def test_raises_for_unknown_extension(self):
        try:
            read_file("test.xyz")
            assert False, "应该抛出异常"
        except ValueError as e:
            assert "不支持的文件格式" in str(e)


class TestPDFReader:
    def test_read_pdf(self):
        import sys

        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "PDF 测试内容"
        mock_pdf.open.return_value.__enter__.return_value.pages = [mock_page]
        with patch.dict(sys.modules, {"pdfplumber": mock_pdf}):
            with patch("pathlib.Path.exists", return_value=True):
                content = read_file("test.pdf")
                assert "PDF 测试内容" in content


class TestDocxReader:
    def test_read_docx(self):
        import sys

        mock_doc = MagicMock()
        mock_doc.return_value.paragraphs = [
            type("P", (), {"text": "段落一"})(),
            type("P", (), {"text": ""})(),
            type("P", (), {"text": "段落二"})(),
        ]
        with patch.dict(sys.modules, {"docx": MagicMock(Document=mock_doc)}):
            with patch("pathlib.Path.exists", return_value=True):
                content = read_file("test.docx")
                assert "段落一" in content
                assert "段落二" in content


class TestImageReader:
    def test_read_image_delegates_to_llm(self):
        with patch(
            "llm_wiki.reader._read_image", return_value="图片中的文字内容"
        ) as mock_fn:
            with patch("pathlib.Path.exists", return_value=True):
                content = read_file("test.png")
                assert content == "图片中的文字内容"
                mock_fn.assert_called_once()
