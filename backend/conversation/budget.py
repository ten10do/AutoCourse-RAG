from __future__ import annotations

from .models import ConversationTurn


ROLE_OVERHEAD_CHARS = 12
SUMMARY_OVERHEAD_CHARS = 12


def estimate_context_chars(
    current_question: str,
    summary: str,
    retained_turns: list[ConversationTurn],
) -> int:
    turn_chars = sum(
        len(turn.content) + ROLE_OVERHEAD_CHARS
        for turn in retained_turns
    )
    summary_chars = len(summary) + SUMMARY_OVERHEAD_CHARS if summary else 0
    return len(current_question) + turn_chars + summary_chars


def trim_to_context_budget(
    current_question: str,
    summary: str,
    retained_turns: list[ConversationTurn],
    max_context_chars: int,
) -> tuple[str, list[ConversationTurn], bool]:
    bounded_summary = summary
    bounded_turns = list(retained_turns)
    limit_applied = False

    if (
        bounded_summary
        and estimate_context_chars(
            current_question,
            bounded_summary,
            bounded_turns,
        )
        > max_context_chars
    ):
        fixed_size = estimate_context_chars(
            current_question,
            "",
            bounded_turns,
        )
        available = max(0, max_context_chars - fixed_size - SUMMARY_OVERHEAD_CHARS)
        bounded_summary = bounded_summary[:available].rstrip()
        limit_applied = True

    while (
        bounded_turns
        and estimate_context_chars(
            current_question,
            bounded_summary,
            bounded_turns,
        )
        > max_context_chars
    ):
        bounded_turns.pop(0)
        limit_applied = True

    if (
        bounded_summary
        and estimate_context_chars(
            current_question,
            bounded_summary,
            bounded_turns,
        )
        > max_context_chars
    ):
        fixed_size = estimate_context_chars(
            current_question,
            "",
            bounded_turns,
        )
        available = max(0, max_context_chars - fixed_size - SUMMARY_OVERHEAD_CHARS)
        bounded_summary = bounded_summary[:available].rstrip()
        limit_applied = True

    return bounded_summary, bounded_turns, limit_applied
