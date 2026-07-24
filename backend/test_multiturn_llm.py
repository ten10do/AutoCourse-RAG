from types import SimpleNamespace
from unittest.mock import patch

import pytest

from backend import light_rag_core, llm_client


def test_answer_prompt_separates_history_from_current_retrieval_evidence():
    docs = [
        (
            SimpleNamespace(
                page_content="当前检索证据：积分作用可以消除稳态误差。"
            ),
            0.1,
        )
    ]

    prompt = llm_client.build_prompt(
        "其中积分项有什么作用？",
        docs,
        conversation_summary="较早对话讨论 PID。",
        conversation_history=[
            {"role": "assistant", "content": "历史回答只用于理解指代。"}
        ],
    )

    assert "只用于理解当前问题，不是知识来源" in prompt
    assert "只用于理解指代，不是知识来源" in prompt
    assert "当前检索证据：积分作用可以消除稳态误差。" in prompt
    assert "当前用户问题：\n其中积分项有什么作用？" in prompt
    assert "历史助手回答不能替代本轮参考资料" in prompt


@pytest.mark.parametrize(
    ("provider", "function_name"),
    [
        ("Groq", "generate_with_groq"),
        ("DeepSeek", "generate_with_deepseek"),
    ],
)
def test_both_model_providers_keep_multiturn_arguments_compatible(
    provider,
    function_name,
):
    docs = [(SimpleNamespace(page_content="检索证据"), 0.1)]
    with patch.object(
        llm_client,
        function_name,
        return_value="模型回答",
    ) as provider_call:
        answer = llm_client.generate_llm_answer(
            "当前问题",
            docs,
            provider=provider,
            conversation_summary="摘要",
            conversation_history=[
                {"role": "user", "content": "上一轮问题"}
            ],
        )

    assert answer == "模型回答"
    provider_call.assert_called_once_with(
        "当前问题",
        docs,
        conversation_summary="摘要",
        conversation_history=[
            {"role": "user", "content": "上一轮问题"}
        ],
    )


def test_light_mode_forwards_bounded_context_to_the_shared_llm_client():
    docs = [(SimpleNamespace(page_content="检索证据"), 0.1)]
    with patch.object(
        light_rag_core,
        "generate_llm_answer",
        return_value="回答",
    ) as generate:
        result = light_rag_core.generate_answer(
            "当前问题",
            docs,
            provider="Groq",
            conversation_summary="摘要",
            conversation_history=[
                {"role": "assistant", "content": "最近回答"}
            ],
        )

    assert result == "回答"
    generate.assert_called_once_with(
        "当前问题",
        docs,
        provider="Groq",
        conversation_summary="摘要",
        conversation_history=[
            {"role": "assistant", "content": "最近回答"}
        ],
    )
