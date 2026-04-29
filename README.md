# siyuan-llm-wiki

基于 [Andrej Karpathy 的 llm-wiki 方法论](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) 构建的思源笔记知识库工具。

通过 LLM 将来源文档深度整合到[思源笔记](https://b3log.org/siyuan/)中，构建可积累的结构化知识库。核心思路：LLM 不只是检索原始文档，而是**增量构建和维护一个持久化的 Wiki** — 摘要、实体页、概念页、交叉引用全部由 LLM 自动生成和维护，知识随每次摄入不断积累。

## 安装

```bash
git clone https://github.com/yangguoquan001/siyuan-llm-wiki.git
cd siyuan-llm-wiki
uv pip install -e .
```

## 环境变量

```powershell
# 必填
$env:SIYUAN_TOKEN = "你的思源 API Token"     # 思源 → 设置 → 关于
$env:OPENAI_API_KEY = "sk-..."                # 或 ANTHROPIC_API_KEY

# 可选
$env:SIYUAN_URL = "http://127.0.0.1:6806"     # 默认值
$env:LLM_PROVIDER = "openai"                   # openai / anthropic
$env:LLM_MODEL = "gpt-4o"                      # 模型名称
```

## 使用

### 查看可用笔记本

```powershell
siyuan-llm-wiki notebooks
```

从输出中复制目标笔记本 ID，设置为环境变量：

```powershell
$env:SIYUAN_NOTEBOOK = "20210817205410-2kvfpfn"
```

### 初始化

在思源笔记本中创建 Wiki 基础结构（schema、index、log）：

```powershell
siyuan-llm-wiki init
```

### 摄入来源文档

将来源文档放入 `raw/` 目录，然后：

```powershell
siyuan-llm-wiki ingest raw/某文章.md
```

支持格式：md / txt / pdf / html / docx / png / jpg

LLM 会：
1. 创建来源摘要页
2. 提取实体和概念，创建或更新对应页面
3. 自动生成 `[[页面名]]` 交叉引用并转换为 `siyuan://blocks/{id}` 超链接
4. 更新索引和操作日志

### 查询知识库

```powershell
siyuan-llm-wiki query "DeepSeek 是什么？"
siyuan-llm-wiki query "比较 GPT 和 Claude" --save    # 保存回答为 Wiki 页面
```

### 健康检查

```powershell
siyuan-llm-wiki lint
```

### 交互模式

```powershell
siyuan-llm-wiki chat
```

支持 `@ingest 文件名`、`@lint` 快捷命令。

## Wiki 结构

```
/{笔记本}/
├── /schema           — 结构约定文档
├── /index            — 索引导航文档
├── /log              — 操作日志
└── /pages/
    ├── /sources/     — 来源摘要
    ├── /entities/    — 实体页（人物、组织、概念等）
    ├── /concepts/    — 概念页
    ├── /comparisons/ — 对比页
    └── /queries/     — 查询存档
```

## 开发

```bash
uv pip install -e ".[dev]"
pytest
```
