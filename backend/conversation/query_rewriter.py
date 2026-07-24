from __future__ import annotations

import re
from typing import Callable, Protocol

from .models import (
    MAX_STANDALONE_QUERY_CHARS,
    ConversationTurn,
    normalize_message_text,
)


class QueryRewriter(Protocol):
    def rewrite(
        self,
        current_question: str,
        summary: str,
        recent_turns: list[ConversationTurn],
        max_chars: int,
    ) -> str:
        ...


def _format_recent_turns(turns: list[ConversationTurn]) -> str:
    labels = {"user": "用户", "assistant": "助手"}
    return "\n".join(
        f"{labels[turn.role]}：{turn.content}"
        for turn in turns
    )


class LlmQueryRewriter:
    def __init__(self, completion: Callable[[str], str]):
        self._completion = completion

    def rewrite(
        self,
        current_question: str,
        summary: str,
        recent_turns: list[ConversationTurn],
        max_chars: int,
    ) -> str:
        prompt = f"""
请把当前课程追问改写为可独立检索的问题。

规则：
- 只使用历史中明确出现的信息；
- 消解“其中”“它”“该概念”等指代；
- 不改变用户原意，不新增主题；
- 已经完整的问题保持原意；
- 无法可靠消解时原样返回；
- 最长 {max_chars} 个字符。

<conversation_summary>
{summary or "无"}
</conversation_summary>

<recent_conversation>
{_format_recent_turns(recent_turns) or "无"}
</recent_conversation>

<current_question>
{current_question}
</current_question>

只输出改写后的问题。
""".strip()
        return self._completion(prompt)


def normalize_standalone_query(value: str, max_chars: int) -> str:
    if not isinstance(value, str):
        return ""
    normalized = normalize_message_text(value)
    normalized = re.sub(
        r"^(?:独立问题|改写结果|standalone[_ ]query)\s*[:：]\s*",
        "",
        normalized,
        flags=re.IGNORECASE,
    )
    return normalized.strip("\"'")[:max_chars].rstrip()


def _extract_topic(text: str) -> str:
    text = text.strip("？?。 ")
    patterns = [
        r"^什么是(.+)$",
        r"^(.+?)(?:包括|包含|由)哪些(?:阶段|环节|部分|内容).*$",
        r"^请(?:介绍|说明|解释)(.+)$",
    ]
    topic = ""
    for pattern in patterns:
        match = re.match(pattern, text)
        if match:
            topic = match.group(1)
            break

    if not topic:
        pid_match = re.search(r"PID\s*控制(?:器)?", text, re.IGNORECASE)
        plc_match = re.search(r"PLC\s*的?扫描周期", text, re.IGNORECASE)
        if pid_match:
            topic = pid_match.group(0)
        elif plc_match:
            topic = plc_match.group(0)

    topic = normalize_message_text(topic)
    topic = re.sub(r"PLC\s*的\s*扫描周期", "PLC 扫描周期", topic, flags=re.I)
    if re.fullmatch(r"PID\s*控制", topic, flags=re.I):
        topic = "PID 控制器"
    return topic[:120].strip()


def _extract_recent_user_topic(
    turns: list[ConversationTurn],
    summary: str = "",
) -> str:
    user_turns = [
        turn.content
        for turn in turns
        if turn.role == "user"
    ]
    detail = ""
    if user_turns:
        detail_match = re.search(
            r"(积分项|积分环节|比例项|比例环节|微分项|微分环节)",
            user_turns[-1],
        )
        if detail_match:
            detail = detail_match.group(1)

    topic = ""
    for text in reversed(user_turns):
        topic = _extract_topic(text)
        if topic:
            break

    if not topic:
        topic = _extract_topic(summary)

    if detail and re.search(r"\bPID\b", topic, re.IGNORECASE):
        return f"{topic}的{detail}"
    return topic


def deterministic_rewrite(
    current_question: str,
    recent_turns: list[ConversationTurn],
    max_chars: int = MAX_STANDALONE_QUERY_CHARS,
    summary: str = "",
) -> tuple[str, str]:
    question = normalize_message_text(current_question)
    pronoun_pattern = r"(?:其中|它|其|该(?:概念|方法|过程|环节)?|上述|这个)"
    if not re.search(pronoun_pattern, question):
        return question[:max_chars], "unchanged"

    topic = _extract_recent_user_topic(recent_turns, summary)
    if not topic:
        return question[:max_chars], "unresolved"

    if question.startswith("其中"):
        remainder = question[len("其中") :]
        rewritten = f"{topic}中的{remainder}"
    elif question.startswith("它"):
        rewritten = topic + question[len("它") :]
    else:
        rewritten = re.sub(pronoun_pattern, topic, question, count=1)

    return normalize_standalone_query(rewritten, max_chars), "fallback"
