"""Schema 管理 — 加载和生成 Wiki 结构约定文档。"""

from pathlib import Path

DEFAULT_SCHEMA = """# Wiki 结构约定

## 目录结构

Wiki 页面按类型存放在不同子目录中：

```
pages/
├── sources/       # 来源摘要页 — 每篇来源文档的提炼
├── entities/      # 实体页 — 人、组织、地点、作品等
├── concepts/      # 概念页 — 理论、思想、主题、方法等
├── comparisons/   # 对比页 — 多个实体/概念的对比分析
├── overviews/     # 综述页 — 某领域的整体性概述
└── queries/       # 查询存档 — 有价值的问答记录
```

## 页面类型与内容要求

### 来源摘要页 (`pages/sources/source-xxx.md`)
每条来源摄入时生成，内容必须包含：
- **基本信息**: 标题、类型（文章/论文/视频/播客等）、来源出处、日期
- **关键要点**: 5-8 条，每条 2-3 句话展开，不是简单的短语罗列
- **与已有知识的关联**: 引用相关的实体页、概念页（用 [[页面名]] 格式）
- **不少于 200 字**

### 实体页 (`pages/entities/实体名.md`)
记录一个具体实体（人、组织、地点、作品等）的综合信息，内容必须包含：
- **定义**: 该实体是什么（1-2 句话），别名或英文名（如有）
- **详细描述**: 2-3 个自然段，深入介绍这个实体
- **关键属性**: 列表形式，每条属性附带简要说明
- **关系网络**: 与该实体相关的其他实体和概念（用 [[页面名]] 链接）
- **时间线**: 如果该实体有发展历程，按时间顺序列出关键事件
- **不少于 300 字**

### 概念页 (`pages/concepts/概念名.md`)
深入分析一个抽象概念、理论或主题，内容必须包含：
- **定义**: 清晰的概念定义（1-2 段），如有不同定义需一并列出
- **详细解释**: 2-3 个自然段，从不同角度剖析这个概念
- **具体实例**: 2-3 个真实案例或场景说明
- **不同观点**: 学术界或实践中对该概念的不同理解和流派
- **实践应用**: 这个概念在现实中有何应用
- **局限与争议**: 该概念的局限性和存在的争议（如有）
- **不少于 300 字**

### 对比页 (`pages/comparisons/对比-xxx.md`)
对比分析，内容必须包含：
- 对比维度的表格或结构化列表
- 每个维度的详细说明
- 总结性分析

### 综述页 (`pages/overviews/综述-xxx.md`)
领域概述，内容必须包含：
- 领域定义和范围
- 核心概念和关键实体的概述
- 发展脉络
- 当前状态和趋势

## 页面命名规范

- 使用中文命名，简洁明了
- 来源摘要页: `source-来源名称.md`（放在 `pages/sources/` 下）
- 实体页: `实体名称.md`（放在 `pages/entities/` 下）
- 概念页: `概念名称.md`（放在 `pages/concepts/` 下）
- 对比页: `对比-xxx.md`（放在 `pages/comparisons/` 下）
- 综述页: `综述-xxx.md`（放在 `pages/overviews/` 下）
- 页面之间使用 `[[页面名]]` 进行交叉引用，不带 `.md` 扩展名也不带子目录前缀

## 页面结构规范

每个页面应包含：
1. 页面标题（一级标题）
2. 多个 `##` 分段（如"## 基本信息"、"## 详细描述"、"## 关键要点"、"## 相关页面"等）
3. 段落之间有空行
4. 底部：`## 相关页面` 小节，列出交叉引用的链接

## 索引规范

index.md 按类别组织，格式如下：

```
# 索引

## 来源
- [[source-xxx]]: 一句话描述，注明类型和日期

## 实体
- [[实体名]]: 一句话描述，注明类型（人物/组织/地点等）

## 概念
- [[概念名]]: 一句话描述，注明领域

## 对比
- [[对比-xxx]]: 对比的双方和维度

## 综述
- [[综述-xxx]]: 领域概述

## 查询存档
- [[query-xxx]]: 原始问题和一句话摘要
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
