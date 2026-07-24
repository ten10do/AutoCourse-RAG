import os
from pathlib import Path

from dotenv import load_dotenv


GROQ_MODEL = "llama-3.1-8b-instant"
DEEPSEEK_MODEL = "deepseek-chat"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")


def build_prompt(
    question: str,
    docs,
    conversation_summary: str | None = None,
    conversation_history: list[dict] | None = None,
):
    context = "\n\n".join(
        [
            f"参考片段 {i + 1}：\n{doc.page_content}"
            for i, (doc, score) in enumerate(docs)
        ]
    )

    conversation_parts = []
    if conversation_summary:
        conversation_parts.append(
            "较早对话摘要（只用于理解当前问题，不是知识来源）：\n"
            + conversation_summary
        )
    if conversation_history:
        labels = {"user": "用户", "assistant": "助手"}
        history_text = "\n".join(
            f"{labels.get(item.get('role'), '消息')}：{item.get('content', '')}"
            for item in conversation_history
        )
        conversation_parts.append(
            "最近对话（只用于理解指代，不是知识来源）：\n"
            + history_text
        )
    conversation_context = (
        "\n\n".join(conversation_parts)
        if conversation_parts
        else "无"
    )

    return f"""
你是一个自动化专业课程助教。

请严格根据下面的参考资料回答用户问题。
如果参考资料中没有相关信息，请回答：“知识库中没有找到相关内容”。

对话上下文：
{conversation_context}

参考资料：
{context}

当前用户问题：
{question}

回答要求：
1. 用中文回答
2. 解释要适合自动化专业本科生理解
3. 不要编造参考资料中没有的信息
4. 如果涉及自动控制、PLC、传感器、电机等内容，请尽量结合自动化专业背景说明
5. 回答尽量条理清晰
6. 历史助手回答不能替代本轮参考资料
"""


def build_messages(
    question: str,
    docs,
    conversation_summary: str | None = None,
    conversation_history: list[dict] | None = None,
):
    return [
        {
            "role": "system",
            "content": "你是一个严谨的自动化专业课程助教，只能根据给定资料回答。"
        },
        {
            "role": "user",
            "content": build_prompt(
                question,
                docs,
                conversation_summary=conversation_summary,
                conversation_history=conversation_history,
            )
        }
    ]


def generate_with_groq(
    question: str,
    docs,
    conversation_summary: str | None = None,
    conversation_history: list[dict] | None = None,
):
    from groq import Groq

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError("没有找到 GROQ_API_KEY，请检查 .env 文件。")

    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=build_messages(
            question,
            docs,
            conversation_summary=conversation_summary,
            conversation_history=conversation_history,
        ),
        temperature=0.2
    )

    return response.choices[0].message.content


def generate_with_deepseek(
    question: str,
    docs,
    conversation_summary: str | None = None,
    conversation_history: list[dict] | None = None,
):
    from openai import OpenAI

    api_key = os.getenv("DEEPSEEK_API_KEY")

    if not api_key:
        raise ValueError("没有找到 DEEPSEEK_API_KEY，请检查 .env 文件。")

    client = OpenAI(
        api_key=api_key,
        base_url=DEEPSEEK_BASE_URL
    )
    response = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=build_messages(
            question,
            docs,
            conversation_summary=conversation_summary,
            conversation_history=conversation_history,
        ),
        temperature=0.2
    )

    return response.choices[0].message.content


def generate_llm_answer(
    question: str,
    docs,
    provider: str = "Groq",
    conversation_summary: str | None = None,
    conversation_history: list[dict] | None = None,
):
    if provider == "Groq":
        return generate_with_groq(
            question,
            docs,
            conversation_summary=conversation_summary,
            conversation_history=conversation_history,
        )

    if provider == "DeepSeek":
        return generate_with_deepseek(
            question,
            docs,
            conversation_summary=conversation_summary,
            conversation_history=conversation_history,
        )

    raise ValueError("不支持的大模型服务，请选择 Groq 或 DeepSeek。")


def generate_context_text(prompt: str, provider: str = "Groq"):
    messages = [
        {
            "role": "system",
            "content": (
                "你只负责压缩课程对话或改写检索问题。"
                "不得新增历史中不存在的事实，只输出任务要求的文本。"
            ),
        },
        {"role": "user", "content": prompt},
    ]

    if provider == "Groq":
        from groq import Groq

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("没有找到 GROQ_API_KEY，请检查运行环境。")
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=0.0,
        )
        return response.choices[0].message.content

    if provider == "DeepSeek":
        from openai import OpenAI

        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("没有找到 DEEPSEEK_API_KEY，请检查运行环境。")
        client = OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL)
        response = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=messages,
            temperature=0.0,
        )
        return response.choices[0].message.content

    raise ValueError("不支持的大模型服务，请选择 Groq 或 DeepSeek。")
