import os
from unittest.mock import patch, MagicMock
from siyuan_llm_wiki.llm import chat, get_client


class TestGetClient:
    def test_openai_client(self):
        with patch.dict(
            os.environ, {"LLM_PROVIDER": "openai", "OPENAI_API_KEY": "sk-test"}
        ):
            with patch("siyuan_llm_wiki.llm.OpenAI") as mock_openai:
                get_client()
                mock_openai.assert_called_once()

    def test_anthropic_client(self):
        with patch.dict(
            os.environ, {"LLM_PROVIDER": "anthropic", "ANTHROPIC_API_KEY": "sk-test"}
        ):
            with patch("siyuan_llm_wiki.llm.Anthropic") as mock_anthropic:
                get_client()
                mock_anthropic.assert_called_once()

    def test_invalid_provider_raises(self):
        with patch.dict(os.environ, {"LLM_PROVIDER": "invalid"}):
            try:
                get_client()
                assert False, "should raise"
            except ValueError as e:
                assert "不支持的 LLM 提供商" in str(e)


class TestChat:
    def test_chat_openai(self):
        with patch.dict(
            os.environ, {"LLM_PROVIDER": "openai", "OPENAI_API_KEY": "sk-test"}
        ):
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "你好，这是回复"
            mock_client.chat.completions.create.return_value = mock_response

            with patch("siyuan_llm_wiki.llm.get_client", return_value=mock_client):
                result = chat("你是一个助手", "你好")
                assert result == "你好，这是回复"

    def test_chat_anthropic(self):
        with patch.dict(
            os.environ, {"LLM_PROVIDER": "anthropic", "ANTHROPIC_API_KEY": "sk-test"}
        ):
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.content = [MagicMock()]
            mock_response.content[0].text = "你好，这是 Claude 的回复"
            mock_client.messages.create.return_value = mock_response

            with patch("siyuan_llm_wiki.llm.get_client", return_value=mock_client):
                result = chat("你是一个助手", "你好")
                assert result == "你好，这是 Claude 的回复"

    def test_chat_retry_on_failure(self):
        with patch.dict(
            os.environ, {"LLM_PROVIDER": "openai", "OPENAI_API_KEY": "sk-test"}
        ):
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "重试后成功"

            mock_client.chat.completions.create.side_effect = [
                Exception("API 错误"),
                Exception("API 错误"),
                mock_response,
            ]

            with patch("siyuan_llm_wiki.llm.get_client", return_value=mock_client):
                result = chat("你是一个助手", "你好")
                assert result == "重试后成功"
                assert mock_client.chat.completions.create.call_count == 3
