from unittest.mock import MagicMock


def make_mock_client():
    """创建带内存存储的模拟 SiYuan 客户端，供各测试模块共享。"""
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
                docs[key[6:]] = markdown
                break

    def _export_md_content(block_id):
        for key, val in list(docs.items()):
            if val == block_id and key.startswith("__id__"):
                return docs.get(key[6:], "")
        for path in docs:
            if not path.startswith("__id__") and docs.get(f"__id__{path}") == block_id:
                return docs.get(path, "")
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
