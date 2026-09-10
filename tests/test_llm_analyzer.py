from unittest.mock import patch

import app.services.llm_analyzer as llm_analyzer


def test_llm_disabled_returns_fallback():
    """LLM 关闭时，应该直接返回降级结果。"""
    representative_errors = [
        {
            "line": "ERROR request timeout",
            "error_type": "超时",
            "severity": "P2",
            "context": ["ERROR request timeout"],
        }
    ]

    with patch.object(
        llm_analyzer,
        "ENABLE_LLM",
        False,
    ):
        result = llm_analyzer.analyze_with_llm(
            representative_errors=representative_errors,
            historical_cases=[],
        )

    assert result["available"] is False
    assert result["reason"] == "LLM disabled"
    assert result["possible_root_cause"] == ""
    assert result["evidence"] == []
    assert result["suggestions"] == []


def test_no_error_logs_returns_fallback():
    """没有代表性异常时，不应该调用 LLM。"""
    with patch.object(
        llm_analyzer,
        "ENABLE_LLM",
        True,
    ):
        with patch.object(
            llm_analyzer,
            "get_llm",
        ) as mock_get_llm:
            result = llm_analyzer.analyze_with_llm(
                representative_errors=[],
                historical_cases=[],
            )

    assert result["available"] is False
    assert result["reason"] == "no error logs"
    mock_get_llm.assert_not_called()


def test_llm_exception_is_degraded():
    """LLM 调用异常时，整个分析流程不应该崩溃。"""
    representative_errors = [
        {
            "line": "ERROR database connection refused",
            "error_type": "数据库连接失败",
            "severity": "P1",
            "context": [
                "INFO application started",
                "ERROR database connection refused",
            ],
        }
    ]

    fake_llm = object()

    with patch.object(
        llm_analyzer,
        "ENABLE_LLM",
        True,
    ):
        with patch.object(
            llm_analyzer,
            "get_llm",
            return_value=fake_llm,
        ):
            with patch(
                "app.services.llm_analyzer.ChatPromptTemplate.from_messages"
            ) as mock_prompt:
                fake_prompt = mock_prompt.return_value

                fake_prompt.__or__.return_value.invoke.side_effect = (
                    RuntimeError("fake api error")
                )

                result = llm_analyzer.analyze_with_llm(
                    representative_errors=representative_errors,
                    historical_cases=[],
                )

    assert result["available"] is False
    assert result["reason"] == "LLM analysis failed: RuntimeError"
    assert result["possible_root_cause"] == ""
    assert result["evidence"] == []
    assert result["confidence"] == ""
    assert result["suggestions"] == []