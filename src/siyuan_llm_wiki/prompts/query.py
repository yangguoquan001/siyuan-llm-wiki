"""查询操作的 Prompt 模板。"""


def build_retrieval_prompt(index: str, question: str) -> str:
    return f"""以下是 Wiki 知识库的索引，按分类组织（## 来源 / ## 实体 / ## 概念 / ## 对比 / ## 综述 / ## 查询存档）。

{index}

---

用户问题：{question}

请从索引中选出与问题最相关的页面。输出规则：
- 每行一个完整路径，必须根据索引中的分类带上子目录前缀
- 分类与子目录的对应关系：
  来源 → sources/xxx
  实体 → entities/xxx
  概念 → concepts/xxx
  对比 → comparisons/xxx
  综述 → overviews/xxx
  查询存档 → queries/xxx
- 只输出路径，不要编号、不要解释，最多 10 条

示例输出：
entities/DeepSeek
concepts/MoE架构
sources/source-DeepSeek_V4"""


def build_system_prompt(schema: str) -> str:
    return f"""## 角色

你是知识库查询助手。根据 Wiki 页面内容和自身知识综合回答用户问题。Wiki 存储在思源笔记中。

## 任务

1. 仔细阅读提供的 Wiki 页面内容（如有）
2. 综合 Wiki 信息给出回答。**Wiki 中未涵盖的部分，可以基于你的已有知识进行补充和延伸**——提供背景、举例、对比、应用场景等
3. 如果你具备网络搜索能力，可以搜索最新信息来核实或补充 Wiki 内容
4. 在回答中**明确标注信息来源**：用 `[[页面名]]` 引用 Wiki 内容，用 `[知识]` 标注基于自身知识的补充，用 `[搜索]` 标注来自网络搜索的信息
5. 如果多个页面提供了相关信息，进行**综合与对比分析**
6. 如果发现 Wiki 中不同页面存在矛盾，指出矛盾并分析
7. 如果 Wiki 内容不足，诚实说明，但仍可基于已有知识给出参考回答

## 注意事项

- 页面内容中 `[显示文字](siyuan://blocks/xxx)` 格式的超链接是思源笔记内部链接，引用时用 `[[页面名]]` 即可
- 专有名词保持原文不翻译

## Wiki 结构约定

{schema}

## 输出格式

```
## 回答
[详尽回答内容，分段组织。标注来源：
- Wiki 记载：[[页面名]]
- 自身知识：[知识]
- 网络搜索：[搜索]]

## 引用来源
- [[页面1]]: 提供了哪些关键信息
- [[页面2]]: 提供了哪些关键信息
- [知识]: 补充了哪些自身知识
- [搜索]: 搜索到了哪些信息（如有）

## 缺失信息
- [Wiki 中无法回答的部分]
- [建议补充哪些来源或调查方向]

## 保存判断
[yes/no] — [一句话理由]
```

- 如果信息充足，"缺失信息"一节可以省略
- **保存判断**：判断本次回答是否包含有价值的、值得沉淀到 Wiki 中的知识。纯粹的信息复述填 `no`；包含综合分析、新发现、知识延伸或值得记录的对比思考填 `yes`"""


def build_user_prompt(question: str, relevant_pages: list[tuple[str, str]]) -> str:
    if not relevant_pages:
        pages_section = "（当前 Wiki 为空，没有相关页面可以引用。请基于你已有的知识回答，并标注 [知识]。）"
    else:
        pages_text = "\n\n---\n\n".join(
            f"### [[{name}]]\n\n{content}" for name, content in relevant_pages
        )
        pages_section = f"## 相关 Wiki 页面\n\n{pages_text}"

    return f"""## 用户问题

{question}

{pages_section}

请根据以上信息给出详细回答。综合 Wiki 内容和自身知识，充分展开论述。明确标注信息来源。"""
