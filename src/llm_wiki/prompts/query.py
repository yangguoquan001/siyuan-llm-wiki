"""查询操作的中文 Prompt 模板。"""


def build_system_prompt(schema: str) -> str:
    return f"""你是一个知识库查询助手。你会收到用户的问题以及 Wiki 知识库中的相关页面内容。

## Wiki 结构约定

{schema}

## 你的任务

1. 仔细阅读提供的 Wiki 页面内容
2. 综合这些信息回答用户的问题
3. 在回答中引用相关的 Wiki 页面（使用 `[[页面名]]` 格式）
4. 如果当前 Wiki 内容不足以完整回答问题，诚实说明哪些信息缺失
5. 如果发现 Wiki 中的内容存在矛盾，指出矛盾所在并分析可能的原因

## 输出格式

```
## 回答
[你的回答内容。引用来源时使用 [[页面名]] 格式。]

## 引用来源
- [[页面1]]: 提供了哪些关键信息
- [[页面2]]: 提供了哪些关键信息

## 缺失信息（如适用）
- 哪些问题当前 Wiki 无法回答
- 建议补充哪些来源或调查方向
```
"""


def build_user_prompt(question: str, relevant_pages: list[tuple[str, str]]) -> str:
    if not relevant_pages:
        pages_section = "（当前 Wiki 为空，没有相关页面可以引用）"
    else:
        pages_text = "\n\n---\n\n".join(
            f"### [[{name.replace('.md', '')}]]\n\n{content}"
            for name, content in relevant_pages
        )
        pages_section = f"## 相关 Wiki 页面\n\n{pages_text}"

    return f"""## 用户问题

{question}

{pages_section}

请根据以上信息回答问题。如果当前 Wiki 信息不足，请诚实说明，并建议如何补充相关知识。"""
