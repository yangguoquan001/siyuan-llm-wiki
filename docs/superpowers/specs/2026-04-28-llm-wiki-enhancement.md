# LLM Wiki 增强 — 页面归类与内容详实度提升

**日期**: 2026-04-28  
**状态**: 待实现  
**基于**: V1 已完成的 llm-wiki 工具

## 改动 1: 子目录归类

### 目标
将 pages/ 下平铺的页面按类型分到子目录，便于浏览和区分。

### pages/ 新结构

```
pages/
├── sources/       # 来源摘要页
├── entities/      # 实体页（人、组织、地点等）
├── concepts/      # 概念页（理论、主题等）
├── comparisons/   # 对比页
├── overviews/     # 综述页
└── queries/       # 查询存档
```

### 涉及修改

1. **schema.py** — DEFAULT_SCHEMA 更新页面路径规范，所有 `pages/xxx.md` 改为 `pages/类型/xxx.md`
2. **prompts/ingest.py** — 系统提示词中的输出格式更新路径
3. **prompts/query.py** — 查询时搜索所有子目录
4. **prompts/lint.py** — 检查时涵盖子目录
5. **operations/query.py** — 保存查询结果到 `pages/queries/`，搜索适配子目录

## 改动 2: 内容详实度

### 目标
解决 LLM 生成内容过于简单（一句话页面）的问题，要求生成详尽、有深度的内容。

### 来源摘要页要求
- 标题、来源类型、日期
- 5-8 个关键要点，每条 2-3 句展开
- 与已有知识的关联（引用具体页面）
- 不少于 200 字

### 实体页要求
- 定义和基本属性
- 详细描述（2-3 段）
- 关键属性列表
- 与其他实体/概念的关系
- 时间线（如适用）
- 不少于 300 字

### 概念页要求
- 定义（1-2 段）
- 详细解释（2-3 段）
- 2-3 个具体实例
- 不同观点/流派
- 实际应用
- 不少于 300 字

### Lint 新增检查
- 内容贫瘠：标记 <200 字的页面
- 结构缺失：标记无分段结构（只有一个 `#` 标题）的页面

## 涉及文件清单

| 文件 | 改动类型 |
|------|----------|
| `src/llm_wiki/schema.py` | 修改 DEFAULT_SCHEMA |
| `src/llm_wiki/prompts/ingest.py` | 重写 prompt 模板 |
| `src/llm_wiki/prompts/query.py` | 更新路径引用 |
| `src/llm_wiki/prompts/lint.py` | 新增内容质量检查 |
| `src/llm_wiki/operations/query.py` | 保存路径 + 搜索逻辑 |
| `tests/test_schema.py` | 更新测试预期 |
| `tests/test_operations_query.py` | 更新测试预期 |
