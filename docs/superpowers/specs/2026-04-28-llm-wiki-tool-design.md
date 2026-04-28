# LLM Wiki 工具 — 设计方案

**日期**: 2026-04-28  
**状态**: 待实现  
**基于**: [llm-wiki.md](../../../llm-wiki.md) 方法论

## 1. 项目目标

基于 LLM Wiki 方法论，构建一个 Python CLI 工具，帮助用户通过 LLM 增量构建和维护个人知识库（Wiki）。工具负责文件编排和 Prompt 管理，所有语义理解（摘要、交叉引用、矛盾检测）由 LLM 完成。

## 2. 技术栈

| 层级 | 选择 | 说明 |
|------|------|------|
| 语言 | Python 3.11+ | |
| 包管理 | uv | 虚拟环境 + 依赖管理 |
| CLI 框架 | Click | 最成熟的 Python CLI 库 |
| LLM API | openai SDK + anthropic SDK | 支持 OpenAI 和 Claude 系列模型 |
| PDF 解析 | pdfplumber | 提取文本和表格 |
| HTML 解析 | beautifulsoup4 | 提取正文内容 |
| Word 解析 | python-docx | 提取段落文本 |
| 图片处理 | Pillow | 预处理后传给视觉 LLM |

## 3. 目录结构

```
my-llm-wiki/
├── pyproject.toml
├── src/
│   └── llm_wiki/
│       ├── __init__.py
│       ├── cli.py              # Click CLI 入口
│       ├── wiki.py             # Wiki 文件系统操作（读写页面/index/log）
│       ├── schema.py           # Schema 加载与默认模板
│       ├── llm.py              # LLM 客户端抽象（OpenAI + Claude）
│       ├── reader.py           # 文件格式读取器（pdf/html/docx/image/txt）
│       ├── prompts/
│       │   ├── __init__.py
│       │   ├── ingest.py       # 摄入操作中文 Prompt
│       │   ├── query.py        # 查询操作中文 Prompt
│       │   └── lint.py         # 健康检查中文 Prompt
│       └── operations/
│           ├── __init__.py
│           ├── ingest.py       # 摄入流程编排
│           ├── query.py        # 查询流程编排
│           └── lint.py         # 检查流程编排
├── wiki/                       # 默认 Wiki 目录（init 命令创建）
│   ├── schema.md               # AGENTS.md 风格的结构约定
│   ├── index.md                # 内容索引
│   ├── log.md                  # 操作日志
│   └── pages/                  # Wiki 页面
├── raw/                        # 原始来源文档（用户自行放入）
└── tests/
    ├── test_wiki.py
    ├── test_reader.py
    └── test_operations.py
```

## 4. 核心架构

### 4.1 数据流

```
用户 → CLI → operations/ → reader.py (解析来源文件)
                         → wiki.py (读 wiki 文件)
                         → llm.py (调用 LLM API，传入中文 prompt)
                         → wiki.py (写回 wiki 文件)
```

### 4.2 模块职责

**`llm.py`** — LLM 客户端抽象
- 统一接口：`chat(messages, model)` → `str`
- 支持 OpenAI (`openai` SDK) 和 Anthropic (`anthropic` SDK)
- 通过环境变量配置：`LLM_PROVIDER`、`OPENAI_API_KEY`、`ANTHROPIC_API_KEY`、`LLM_MODEL`
- 视觉模型支持：当传入图片时自动路由到视觉模型

**`wiki.py`** — Wiki 文件系统操作
- 初始化 wiki 目录结构 (`init`)
- 读写 wiki 页面、`index.md`、`log.md`
- 搜索 wiki 页面（遍历 pages/ 目录，按标题/内容简单匹配）

**`reader.py`** — 多格式文件读取器
- 统一接口：`read(file_path)` → `str` (纯文本)
- 支持格式：`.md`, `.txt`, `.pdf`, `.html`, `.docx`, `.png`, `.jpg`, `.jpeg`
- 图片通过视觉 LLM 提取文字

**`schema.py`** — Schema 管理
- 加载 `wiki/schema.md` 作为系统提示词的一部分
- 提供默认 schema 模板（中文）

**`prompts/`** — 中文 Prompt 模板
- `ingest.py`: 摄入文档的系统提示词和用户提示词模板
- `query.py`: 查询 wiki 的系统提示词模板
- `lint.py`: 健康检查的系统提示词模板

**`operations/`** — 操作编排
- `ingest.py`: 读取来源 → 调用 LLM 生成/更新 wiki 页面 → 更新 index/log
- `query.py`: 读取 index → 匹配相关页面 → 调用 LLM 生成回答
- `lint.py`: 扫描所有页面 → 调用 LLM 检测问题 → 输出报告

## 5. CLI 命令

| 命令 | 说明 |
|------|------|
| `llm-wiki init [--wiki-dir WIKI_DIR] [--raw-dir RAW_DIR]` | 初始化 wiki 目录结构，生成默认 schema.md |
| `llm-wiki ingest <source_file>` | 摄入一个来源文件，更新 wiki |
| `llm-wiki query "<question>" [--save]` | 查询 wiki，`--save` 将回答保存为 wiki 页面 |
| `llm-wiki lint` | 健康检查，输出诊断报告 |
| `llm-wiki chat` | 交互式对话模式，持续与 LLM 协同维护 wiki |

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `LLM_PROVIDER` | LLM 提供商：`openai` / `anthropic` | `openai` |
| `LLM_MODEL` | 模型名称 | `gpt-4o` |
| `OPENAI_API_KEY` | OpenAI API 密钥 | - |
| `OPENAI_BASE_URL` | OpenAI API 地址（兼容） | `https://api.openai.com/v1` |
| `ANTHROPIC_API_KEY` | Anthropic API 密钥 | - |
| `LLM_WIKI_DIR` | Wiki 目录路径 | `./wiki` |
| `LLM_RAW_DIR` | 原始来源目录路径 | `./raw` |

## 6. 操作流程详解

### 6.1 Ingest（摄入）

1. 读取 `wiki/schema.md` 作为系统提示词的一部分
2. 调用 `reader.read(source_file)` 解析来源文件为纯文本
3. 调用 LLM，传入来源文本 + 现有 index + 相关页面，指示 LLM：
   - 提取关键信息
   - 生成/更新摘要页
   - 更新相关实体页和概念页
   - 标记与新信息矛盾的内容
   - 添加交叉引用
4. LLM 返回需要创建/更新的页面列表及内容
5. 写入新页面，更新 index.md，追加 log.md
6. 输出变更摘要给用户

### 6.2 Query（查询）

1. 读取 `index.md` 找到相关页面
2. 读取匹配的 wiki 页面内容
3. 调用 LLM，传入问题 + 相关页面内容 + schema
4. LLM 生成回答（含引用来源的 wiki 页面）
5. 如果 `--save`，将回答保存为新的 wiki 页面并更新 index

### 6.3 Lint（检查）

1. 读取所有 wiki 页面
2. 读取 `index.md` 和 `log.md`
3. 调用 LLM，传入所有内容，指示 LLM 检查：
   - 页面间的矛盾
   - 过时声明（被新来源取代的旧信息）
   - 孤立页面（无入站链接）
   - 缺失页面（被引用但不存在）
   - 缺失的交叉引用
   - 可进一步探索的问题和来源建议
4. 输出诊断报告

## 7. 文件格式处理

| 格式 | 解析库 | 处理方式 |
|------|--------|---------|
| `.md` / `.txt` | 原生 | 直接读取 |
| `.pdf` | `pdfplumber` | 逐页提取文本，含表格 |
| `.html` | `beautifulsoup4` | 提取 body 正文，去除 script/style 标签 |
| `.docx` | `python-docx` | 提取所有段落文本，按序拼接 |
| `.png/.jpg/.jpeg` | `Pillow` + visual LLM | 预处理图片，传给视觉模型提取文字描述 |

## 8. Prompt 语言

所有 Prompt 使用**中文**编写，符合用户使用习惯。关键 Prompt 包括：

- **Ingest 系统提示词**：定义 LLM 作为 wiki 维护者的角色、输出格式、页面结构约定
- **Query 系统提示词**：定义 LLM 作为知识库查询助手的角色、引用格式要求
- **Lint 系统提示词**：定义 LLM 作为 wiki 审查者的角色、检查维度

## 9. 错误处理

- LLM API 调用失败：重试 3 次，指数退避
- 文件解析失败：跳过该文件，记录错误到 log
- Wiki 文件写入冲突：先写入临时文件，确认无误后替换
- 配置缺失：给出明确的中文错误提示

## 10. 测试策略

- `test_wiki.py`：测试 wiki 文件系统操作（init、读写页面、索引更新）
- `test_reader.py`：测试各格式文件读取
- `test_operations.py`：测试 ingest/query/lint 流程（需 mock LLM 调用）
