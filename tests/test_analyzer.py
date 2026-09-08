from unittest.mock import patch

from app.analyzer import analyze_log


def test_analyze_log_with_mocked_rag_and_llm() -> None:
    """测试分析流程，同时避免真实调用 RAG 和 LLM。"""
    lines = [
        "2026-09-05 10:00:00 INFO Application started",
        "2026-09-05 10:01:00 WARN Database response is slow",
        "2026-09-05 10:02:00 ERROR database connection refused",
        "2026-09-05 10:03:00 ERROR request timeout after 30 seconds",
        "2026-09-05 10:04:00 ERROR java.lang.OutOfMemoryError: Java heap space",
    ]

    fake_case = {
        "id": "case_test",
        "title": "测试历史案例",
        "error_type": "内存溢出",
        "severity": "P0",
        "content": "这是一个测试历史案例",
    }

    fake_llm_result = {
        "available": True,
        "reason": "",
        "possible_root_cause": "测试可能根因",
        "evidence": ["测试证据"],
        "confidence": "中",
        "suggestions": ["测试建议"],
    }

    with patch(
        "app.analyzer.retrieve_similar_cases",
        return_value=[fake_case],
    ) as mock_retrieve:
        with patch(
            "app.analyzer.analyze_with_llm",
            return_value=fake_llm_result,
        ) as mock_llm:
            result = analyze_log(lines)

    assert result["parse_result"]["total"] == 5
    assert result["error_summary"]["highest_severity"] == "P0"

    representative_errors = result["representative_errors"]
    assert len(representative_errors) == 3
    assert representative_errors[0]["severity"] == "P0"

    historical_cases = result["historical_cases"]
    assert len(historical_cases) == 1
    assert historical_cases[0]["id"] == "case_test"

    assert result["llm_analysis"] == fake_llm_result

    assert mock_retrieve.call_count == 3
    mock_llm.assert_called_once()