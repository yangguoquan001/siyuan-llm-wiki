# LLM Wiki 思源笔记集成 — 设计方案

**日期**: 2026-04-28
**状态**: 已完成
**目标**: 将 LLM Wiki 的输出目标从本地 Markdown 文件改为思源笔记，保持目录结构，支持 `siyuan://blocks/{id}` 超链接跳转。

## 1. 改动范围

### 新增文件
| 文件 | 说明 |
|------|------|
| `src/llm_wiki/siyuan.py` | 思源 HTTP API 客户端 |

### 重写文件
| 文件 | 说明 |
|------|------|
| `src/llm_wiki/wiki.py` | 文件 I/O → 思源 API 调用，保留函数签名 |

### 修改文件
| 文件 | 改动 |
|------|------|
| `cli.py` | 删除 `--wiki-dir`，增加 `--siyuan-url/token/notebook` |
| `schema.py` | DEFAULT_SCHEMA 超链接格式改为 `siyuan://blocks/{id}` |
| `prompts/ingest.py` | 路径格式调整为思源文档树格式 |
| `prompts/query.py` | 引用格式改为思源超链接 |
| `prompts/lint.py` | 同上 |
| `operations/ingest.py` | 增加两遍超链接处理 |
| `operations/query.py` | 搜索改用 SQL API |
| `operations/lint.py` | 读取改用 API |

### 不动文件
- `reader.py` — 多格式解析不变
- `llm.py` — LLM 客户端不变

## 2. siyuan.py 设计

```python
class SiYuanClient:
    def __init__(self, url, token, notebook)
    def create_doc(path, markdown) -> str        # 返回 block_id
    def update_block(id, markdown) -> None
    def get_kramdown(id) -> str
    def get_child_blocks(id) -> list[dict]
    def delete_block(id) -> None
    def sql_query(stmt) -> list[dict]
    def get_ids_by_hpath(path) -> list[str]
    def get_hpath_by_id(id) -> str
    def get_block_attrs(id) -> dict
```

配置来源：
- `SIYUAN_URL` 环境变量，默认 `http://127.0.0.1:6806`
- `SIYUAN_TOKEN` 环境变量（必填）
- `SIYUAN_NOTEBOOK` 环境变量（必填，笔记本 ID）

## 3. wiki.py 重写

保留函数签名，内部改用 SiYuan API：

| 函数 | 实现方式 |
|------|----------|
| `init_wiki()` | 确保笔记本中有 `/schema`、`/index`、`/log` 三份文档 |
| `read_page(name)` | `get_ids_by_hpath` → `get_kramdown` |
| `write_page(name, content)` | 不存在则 `create_doc`（返回 id），存在则 `update_block` |
| `read_index()` | 读取 `/index` 文档 |
| `write_index(content)` | 更新 `/index` 文档 |
| `append_log(entry)` | 读取 `/log` → 追加 → `update_block` |
| `list_pages()` | 递归 `get_child_blocks` 遍历文档树 |

`write_page` 返回创建或更新使用的 block_id，供超链接解析使用。

## 4. 超链接两遍处理（ingest.py）

### 第一遍：创建文档，收集 ID
1. `_parse_operations()` 解析 LLM 输出的页面操作
2. 对每个"创建"操作：`write_page()` → 记录 `{页面名: block_id}`
3. 对每个"更新"操作：`write_page()` → 记录 `{页面名: block_id}`

### 第二遍：替换超链接，写回
1. 构建全局映射表：新创建 ID + 已有页面（通过 SQL 查 title）
2. 扫描所有文档内容中的 `[[页面名]]` 模式
3. 查映射表：
   - 找到 → 替换为 `[页面名](siyuan://blocks/{id})`
   - 未找到 → 保留原样（可能是还不存在的引用）
4. `update_block()` 写回更新后的内容

### 映射策略
- 以页面叶子名称（`实体名`）为 key 查映射表
- 冲突时（同名不同路径）：匹配包含路径前缀的那个
- 已有页面通过 SQL 查询所有文档块，用 title 匹配

## 5. 搜索改造（query.py）

`_find_relevant_pages()` 改为：
```sql
SELECT id, content FROM blocks 
WHERE type = 'd' AND content LIKE '%关键词%'
LIMIT 10
```
通过 `get_kramdown` 获取完整内容。

## 6. CLI 配置

```bash
# 环境变量
SIYUAN_URL=http://127.0.0.1:6806
SIYUAN_TOKEN=your_api_token
SIYUAN_NOTEBOOK=20210817205410-2kvfpfn

# 命令行覆盖
llm-wiki --siyuan-notebook xxx ingest source.pdf
llm-wiki --siyuan-notebook xxx query "问题"
llm-wiki --siyuan-notebook xxx lint
```

删除 `--wiki-dir` 选项和 `LLM_WIKI_DIR` 环境变量。保留 `--raw-dir` / `LLM_RAW_DIR` 用于指定来源文件目录。

## 7. 思源文档树结构

```
/{notebook}/
├── /schema         — 结构约定文档
├── /index          — 索引导航文档（含 siyuan:// 超链接）
├── /log            — 操作日志文档
└── /pages/
    ├── /sources/   — 来源摘要
    ├── /entities/  — 实体页
    ├── /concepts/  — 概念页
    ├── /comparisons/ — 对比页
    ├── /overviews/ — 综述页
    └── /queries/   — 查询存档
```
