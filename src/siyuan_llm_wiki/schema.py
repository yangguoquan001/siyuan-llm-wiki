"""Schema 管理 — 加载和生成 Wiki 结构约定文档。"""


DEFAULT_SCHEMA = """# Wiki 结构约定

## 核心原则

**内容严格来自来源文档，禁止编造。** 文档中没有的信息不要补充，不要为凑字数而发挥。宁可页面短，不可有幻觉。

## 目录结构

```
/pages/
├── /sources/       # 来源摘要页 — 每篇来源文档的提炼
├── /entities/      # 实体页 — 人、组织、地点、作品等
├── /concepts/      # 概念页 — 理论、思想、主题、方法等
├── /comparisons/   # 对比页 — 多个实体/概念的对比分析
├── /overviews/     # 综述页 — 某领域的整体性概述
└── /queries/       # 查询存档 — 有价值的问答记录
```

## 页面类型与内容要求（所有分节均为可选，有则写，无则跳过）

### 来源摘要页 (`/pages/sources/source-xxx`)

从来源文档中提炼的内容：
- **基本信息**: 标题、类型（文章/论文/视频/播客等）、来源出处、日期（如有）
- **关键要点**: 文档中的重要信息点，逐条列出。数量不限，有几点写几点
- **涉及实体/概念**: 文档中提到的实体和概念（用 [[页面名]] 引用）

### 实体页 (`/pages/entities/实体名`)

记录文档中提到的具体实体，按文档中实际提供的信息填写：
- **定义**: 该实体是什么（如有别名或英文名一并写出）
- **属性/特点**: 文档中提到的该实体的特征、参数、功能等
- **关系**: 文档中提及的与其他实体/概念的关联（用 [[页面名]] 引用）

### 概念页 (`/pages/concepts/概念名`)

记录文档中涉及的概念、理论或方法：
- **定义**: 文档给出的定义或描述
- **机制/原理**: 文档中解释的工作机制（如有）
- **特点**: 文档中提到的优点、局限、适用场景等
- **关联**: 文档中提及的相关概念和实体（用 [[页面名]] 引用）

### 对比页 (`/pages/comparisons/对比-xxx`)

当文档涉及多个实体的比较时使用：
- 对比维度列表或表格
- 总结性分析

### 综述页 (`/pages/overviews/综述-xxx`)

当需要某领域整体概述时使用：
- 领域范围和核心内容
- 文档中涉及的关键点

## 页面命名规范

- 使用中文命名，简洁明了
- 来源摘要页: `source-来源名称`（放在 `/pages/sources/` 下）
- 实体页: `实体名称`（放在 `/pages/entities/` 下）
- 概念页: `概念名称`（放在 `/pages/concepts/` 下）
- 对比页: `对比-xxx`（放在 `/pages/comparisons/` 下）
- 综述页: `综述-xxx`（放在 `/pages/overviews/` 下）
- 页面之间使用 `[[页面名]]` 交叉引用

## 页面结构规范

- 不要用与笔记名相同的 `# 一级标题` 开头。直接从 `##` 分段开始
- 多个 `##` 分段组织内容
- 底部可加 `## 相关页面` 列出交叉引用

## 索引规范

index 按类别组织：

```
# 索引

## 来源
- [[source-xxx]]: 一句话描述，注明类型和日期

## 实体
- [[实体名]]: 一句话描述

## 概念
- [[概念名]]: 一句话描述

## 对比
- [[对比-xxx]]: 对比的双方和维度

## 综述
- [[综述-xxx]]: 领域概述

## 查询存档
- [[query-xxx]]: 原始问题和一句话摘要
```

## 超链接说明

- 使用 `[[页面名]]` 引用其他页面
- 系统会自动将 `[[页面名]]` 转换为思源笔记超链接
- 已有的 `[text](siyuan://blocks/{id})` 格式链接保留不动
"""


def load_schema() -> str:
    """加载思源笔记本中的 /schema 文档，如为空则返回默认 schema。"""
    from siyuan_llm_wiki.wiki import read_root_doc

    content = read_root_doc("schema").strip()
    if not content or content in ("schema", "# schema", "# /schema"):
        return DEFAULT_SCHEMA
    return content


def write_default_schema() -> None:
    """如果 /schema 文档不存在或为空，写入默认 schema。"""
    from siyuan_llm_wiki.wiki import read_root_doc, write_root_doc

    content = read_root_doc("schema").strip()
    if not content or content in ("schema", "# schema", "# /schema"):
        write_root_doc("schema", DEFAULT_SCHEMA)
