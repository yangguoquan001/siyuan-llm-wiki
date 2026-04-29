"""LLM 客户端抽象 — 统一 OpenAI 和 Anthropic 接口。"""

import os
import time
from openai import OpenAI
from anthropic import Anthropic

MAX_RETRIES = 3
RETRY_BASE_DELAY = 1.0


def get_client():
    """根据 LLM_PROVIDER 环境变量返回对应的客户端实例。"""
    provider = os.getenv("LLM_PROVIDER", "openai")
    if provider == "openai":
        return OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        )
    elif provider == "anthropic":
        return Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    else:
        raise ValueError(f"不支持的 LLM 提供商: {provider}")


def chat(system_prompt: str, user_prompt: str, model: str | None = None) -> str:
    """发送对话请求，自动重试。"""
    provider = os.getenv("LLM_PROVIDER", "openai")
    model = model or os.getenv("LLM_MODEL", "gpt-4o")
    client = get_client()

    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            if provider == "openai":
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                )
                return response.choices[0].message.content or ""
            elif provider == "anthropic":
                response = client.messages.create(
                    model=model,
                    max_tokens=8192,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}],
                )
                content = response.content
                return content[0].text if content else ""
        except Exception as e:
            last_error = e
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_BASE_DELAY * (2**attempt))
            continue

    raise RuntimeError(f"LLM API 调用失败（重试 {MAX_RETRIES} 次后）: {last_error}")


def chat_with_image(
    system_prompt: str, image_path: str, model: str | None = None
) -> str:
    """发送含图片的对话请求。"""
    import base64
    from pathlib import Path

    provider = os.getenv("LLM_PROVIDER", "openai")
    model = model or os.getenv("LLM_MODEL", "gpt-4o")
    client = get_client()

    image_bytes = Path(image_path).read_bytes()
    ext = Path(image_path).suffix.lower()
    mime_type_map = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg"}
    mime_type = mime_type_map.get(ext.lstrip("."), "image/png")
    base64_image = base64.b64encode(image_bytes).decode("utf-8")

    for attempt in range(MAX_RETRIES):
        try:
            if provider == "anthropic":
                response = client.messages.create(
                    model=model,
                    max_tokens=4096,
                    system=system_prompt,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": mime_type,
                                        "data": base64_image,
                                    },
                                },
                                {"type": "text", "text": system_prompt},
                            ],
                        }
                    ],
                )
                return response.content[0].text if response.content else ""
            else:
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": system_prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:{mime_type};base64,{base64_image}",
                                        "detail": "auto",
                                    },
                                },
                            ],
                        }
                    ],
                )
                return response.choices[0].message.content or ""
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_BASE_DELAY * (2**attempt))
            else:
                raise RuntimeError(f"图片识别 LLM API 调用失败: {e}")

    raise RuntimeError("图片识别失败：已达最大重试次数")
