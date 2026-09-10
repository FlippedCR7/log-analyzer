from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def build_fake_analysis_result() -> dict[str, object]:
    """构造假的分析结果，避免测试调用真实 RAG 和 LLM。"""
    return {
        "parse_result": {
            "total": 3,
            "level_counts": {
                "INFO": 1,
                "WARN": 1,
                "ERROR": 1,
                "UNKNOWN": 0,
            },
            "level_ratios": {
                "INFO": 1 / 3,
                "WARN": 1 / 3,
                "ERROR": 1 / 3,
                "UNKNOWN": 0,
            },
            "timestamps": [
                "2026-09-05 10:00:00",
                "2026-09-05 10:01:00",
                "2026-09-05 10:02:00",
            ],
            "error_lines": [
                "2026-09-05 10:02:00 ERROR request timeout"
            ],
        },
        "error_summary": {
            "数据库连接失败": 0,
            "内存溢出": 0,
            "空指针异常": 0,
            "超时": 1,
            "其他异常": 0,
            "highest_severity": "P2",
        },
        "representative_errors": [
            {
                "index": 2,
                "line": "2026-09-05 10:02:00 ERROR request timeout",
                "error_type": "超时",
                "severity": "P2",
                "context": [
                    "2026-09-05 10:00:00 INFO application started",
                    "2026-09-05 10:01:00 WARN request slow",
                    "2026-09-05 10:02:00 ERROR request timeout",
                ],
            }
        ],
        "historical_cases": [],
        "llm_analysis": {
            "available": False,
            "reason": "LLM disabled",
            "possible_root_cause": "",
            "evidence": [],
            "confidence": "",
            "suggestions": [],
        },
    }


def test_upload_log_success():
    """合法日志文件应该返回 HTTP 200 和业务码 0。"""
    fake_result = build_fake_analysis_result()

    log_content = (
        "2026-09-05 10:00:00 INFO application started\n"
        "2026-09-05 10:01:00 WARN request slow\n"
        "2026-09-05 10:02:00 ERROR request timeout\n"
    )

    with patch(
        "app.main.analyze_log",
        return_value=fake_result,
    ) as mock_analyze:
        response = client.post(
            "/upload",
            files={
                "file": (
                    "sample.log",
                    log_content.encode("utf-8"),
                    "text/plain",
                )
            },
        )

    assert response.status_code == 200

    payload = response.json()

    assert payload["code"] == 0
    assert payload["message"] == "success"
    assert payload["data"]["parse_result"]["total"] == 3
    assert (
        payload["data"]["error_summary"]["highest_severity"]
        == "P2"
    )

    mock_analyze.assert_called_once()


def test_upload_unsupported_file_type():
    """不支持的扩展名应该返回 400 和业务码 4001。"""
    response = client.post(
        "/upload",
        files={
            "file": (
                "sample.csv",
                b"ERROR request timeout",
                "text/csv",
            )
        },
    )

    assert response.status_code == 400

    payload = response.json()

    assert payload["code"] == 4001


def test_upload_invalid_utf8():
    """非 UTF-8 文件应该返回 400 和业务码 4003。"""
    invalid_content = bytes(
        [0xFF, 0xFE, 0xFD, 0xFC]
    )

    response = client.post(
        "/upload",
        files={
            "file": (
                "sample.log",
                invalid_content,
                "text/plain",
            )
        },
    )

    assert response.status_code == 400

    payload = response.json()

    assert payload["code"] == 4003