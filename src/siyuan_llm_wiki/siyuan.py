"""思源笔记 HTTP API 客户端。"""

import json
import urllib.request
import urllib.error
from typing import Any


class SiYuanError(Exception):
    pass


def _get_config(url: str = "", token: str = "", notebook: str = ""):
    import os

    return (
        url or os.getenv("SIYUAN_URL", "http://127.0.0.1:6806"),
        token or os.getenv("SIYUAN_TOKEN", ""),
        notebook or os.getenv("SIYUAN_NOTEBOOK", ""),
    )


def _api(base_url: str, token: str, endpoint: str, payload: dict | None = None) -> Any:
    url = f"{base_url}{endpoint}"
    data = json.dumps(payload).encode("utf-8") if payload else None
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Token {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise SiYuanError(f"HTTP {e.code}: {e.reason}")
    except urllib.error.URLError as e:
        raise SiYuanError(f"连接失败: {e.reason}")

    if body.get("code") != 0:
        raise SiYuanError(f"API 错误 (code={body.get('code')}): {body.get('msg')}")

    return body.get("data")


class SiYuanClient:
    def __init__(self, url: str = "", token: str = "", notebook: str = ""):
        self.url, self.token, self.notebook = _get_config(url, token, notebook)
        if not self.token:
            raise SiYuanError("SIYUAN_TOKEN 未设置")
        if not self.notebook:
            raise SiYuanError("SIYUAN_NOTEBOOK 未设置")

    def _call(self, endpoint: str, payload: dict | None = None) -> Any:
        return _api(self.url, self.token, endpoint, payload)

    # ── 文档操作 ──

    def create_doc(self, path: str, markdown: str) -> str:
        """创建文档，返回文档 block ID。path 以 / 开头。"""
        data = self._call(
            "/api/filetree/createDocWithMd",
            {"notebook": self.notebook, "path": path, "markdown": markdown},
        )
        return str(data)

    def rename_doc(self, path: str, title: str) -> None:
        self._call(
            "/api/filetree/renameDoc",
            {"notebook": self.notebook, "path": path, "title": title},
        )

    def remove_doc(self, path: str) -> None:
        self._call(
            "/api/filetree/removeDoc",
            {"notebook": self.notebook, "path": path},
        )

    def get_ids_by_hpath(self, path: str) -> list[str]:
        """根据人类可读路径获取文档 ID 列表。"""
        data = self._call(
            "/api/filetree/getIDsByHPath",
            {"notebook": self.notebook, "path": path},
        )
        return data if isinstance(data, list) else []

    # ── 块操作 ──

    def update_block(self, block_id: str, markdown: str) -> None:
        self._call(
            "/api/block/updateBlock",
            {"dataType": "markdown", "data": markdown, "id": block_id},
        )

    def get_kramdown(self, block_id: str) -> str:
        """获取块的 kramdown 源码（思源内部 markdown 格式）。"""
        data = self._call("/api/block/getBlockKramdown", {"id": block_id})
        return data.get("kramdown", "") if isinstance(data, dict) else ""

    def get_child_blocks(self, block_id: str) -> list[dict]:
        """获取子块列表。"""
        data = self._call("/api/block/getChildBlocks", {"id": block_id})
        return data if isinstance(data, list) else []

    def delete_block(self, block_id: str) -> None:
        self._call("/api/block/deleteBlock", {"id": block_id})

    def insert_block(
        self, markdown: str, parent_id: str = "", previous_id: str = ""
    ) -> str:
        """在指定位置插入块，返回新块 ID。"""
        payload: dict = {
            "dataType": "markdown",
            "data": markdown,
        }
        if previous_id:
            payload["previousID"] = previous_id
        if parent_id:
            payload["parentID"] = parent_id
        data = self._call("/api/block/insertBlock", payload)
        # 返回第一个 action 的 id
        if isinstance(data, list) and data:
            ops = data[0].get("doOperations", [])
            if ops:
                return ops[0].get("id", "")
        return ""

    def append_block(self, markdown: str, parent_id: str) -> str:
        """在父块末尾追加子块，返回新块 ID。"""
        data = self._call(
            "/api/block/appendBlock",
            {"dataType": "markdown", "data": markdown, "parentID": parent_id},
        )
        if isinstance(data, list) and data:
            ops = data[0].get("doOperations", [])
            if ops:
                return ops[0].get("id", "")
        return ""

    # ── 属性 ──

    def get_block_attrs(self, block_id: str) -> dict:
        data = self._call("/api/attr/getBlockAttrs", {"id": block_id})
        return data if isinstance(data, dict) else {}

    # ── SQL 查询 ──

    def sql_query(self, stmt: str) -> list[dict]:
        data = self._call("/api/query/sql", {"stmt": stmt})
        return data if isinstance(data, list) else []

    # ── 导出 ──

    def export_md_content(self, block_id: str) -> str:
        """导出文档的 Markdown 内容（标准 markdown）。"""
        data = self._call("/api/export/exportMdContent", {"id": block_id})
        if isinstance(data, dict):
            return str(data.get("content", ""))
        return ""


# 全局客户端实例
_client: SiYuanClient | None = None
_config_overrides: dict[str, str] = {}


def set_config(url: str = "", token: str = "", notebook: str = "") -> None:
    """设置全局配置覆盖（优先于环境变量）。"""
    if url:
        _config_overrides["url"] = url
    if token:
        _config_overrides["token"] = token
    if notebook:
        _config_overrides["notebook"] = notebook
    global _client
    _client = None  # 重置，下次 get_client 会用新配置重新创建


def list_notebooks(url: str = "", token: str = "") -> list[dict]:
    """列出所有笔记本（不需要笔记本 ID）。返回 [{id, name, icon, sort, closed}, ...]。"""
    u, t, _ = _get_config(url, token, "")
    if not t:
        raise SiYuanError("SIYUAN_TOKEN 未设置")
    data = _api(u, t, "/api/notebook/lsNotebooks")
    if isinstance(data, dict):
        return data.get("notebooks", [])
    return []


def create_notebook(name: str, url: str = "", token: str = "") -> dict:
    """创建笔记本（不需要笔记本 ID）。返回 {id, name, icon, sort, closed}。"""
    u, t, _ = _get_config(url, token, "")
    if not t:
        raise SiYuanError("SIYUAN_TOKEN 未设置")
    data = _api(u, t, "/api/notebook/createNotebook", {"name": name})
    if isinstance(data, dict):
        nb = data.get("notebook", {})
        return nb
    return {}


def get_client() -> SiYuanClient:
    global _client
    if _client is None:
        _client = SiYuanClient(
            url=_config_overrides.get("url", ""),
            token=_config_overrides.get("token", ""),
            notebook=_config_overrides.get("notebook", ""),
        )
    return _client
