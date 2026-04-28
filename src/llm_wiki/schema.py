"""Schema 管理 — 加载和生成 Wiki 结构约定文档。"""

from pathlib import Path

DEFAULT_SCHEMA = """# Wiki 结构约定

## 页面类型

- **来源摘要页**: 以 `source-` 为前缀，记录单个来源文档的关键信息，包括：标题、来源、日期、关键要点、与已有知识的关联
- **实体页**: 以实体名称为标题，记录关于某个实体（人、组织、地点、概念等）的所有已知信息
- **概念页**: 记录某个概念或主题的深入分析，综合多个来源的观点
- **对比页**: 以 `对比-` 为前缀，对比两个或多个实体/概念的异同
- **综合页**: 以 `综述-` 为前缀，对某个领域的整体性概述

## 页面命名规范

- 使用中文命名，简洁明了
- 来源摘要页: `source-来源名称.md`
- 实体页: `实体名称.md`
- 概念页: `概念名称.md`
- 页面之间使用 `[[页面名]]` 进行交叉引用

## 页面结构规范

每个页面应包含：
1. 页面标题（一级标题）
2. 内容正文，分段组织
3. 底部：相关页面链接列表

## 索引规范

index.md 按类别组织，格式如下：

```
# 索引

## 来源
- [[source-xxx]]: 一句话描述

## 实体
- [[实体名]]: 一句话描述

## 概念
- [[概念名]]: 一句话描述
```
"""


def load_schema(wiki_dir: str) -> str:
    """加载 Wiki 目录中的 schema.md，如果不存在或为空则返回默认 schema。"""
    path = Path(wiki_dir) / "schema.md"
    if path.exists():
        content = path.read_text(encoding="utf-8").strip()
        if content:
            return content
    return DEFAULT_SCHEMA


def write_default_schema(wiki_dir: str) -> None:
    """如果 schema.md 不存在或为空，写入默认 schema。"""
    path = Path(wiki_dir) / "schema.md"
    if not path.exists() or not path.read_text(encoding="utf-8").strip():
        path.write_text(DEFAULT_SCHEMA, encoding="utf-8")
