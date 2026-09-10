from app.services.anomaly_selector import select_representative_errors


def test_select_errors_by_severity():
    """应该按照 P0 -> P1 -> P2 的优先级选择异常。"""
    lines = [
        "2026-09-05 10:00:00 INFO application started",
        "2026-09-05 10:01:00 ERROR request timeout after 30 seconds",
        "2026-09-05 10:02:00 ERROR database connection refused",
        "2026-09-05 10:03:00 ERROR java.lang.OutOfMemoryError: Java heap space",
    ]

    result = select_representative_errors(lines)

    assert len(result) == 3
    assert result[0]["severity"] == "P0"
    assert result[0]["error_type"] == "内存溢出"

    assert result[1]["severity"] == "P1"
    assert result[1]["error_type"] == "数据库连接失败"

    assert result[2]["severity"] == "P2"
    assert result[2]["error_type"] == "超时"


def test_duplicate_error_types_are_removed():
    """相同异常类型应该只保留一条代表性异常。"""
    lines = [
        "2026-09-05 10:00:00 ERROR request timeout after 10 seconds",
        "2026-09-05 10:01:00 ERROR request timeout after 20 seconds",
        "2026-09-05 10:02:00 ERROR request timeout after 30 seconds",
    ]

    result = select_representative_errors(lines)

    assert len(result) == 1
    assert result[0]["error_type"] == "超时"


def test_context_does_not_cross_file_boundary():
    """日志靠近文件开头时，上下文不能越界。"""
    lines = [
        "line 0",
        "2026-09-05 10:00:00 ERROR database connection refused",
        "line 2",
        "line 3",
    ]

    result = select_representative_errors(lines)

    assert len(result) == 1
    assert result[0]["index"] == 1
    assert result[0]["context"] == lines


def test_max_count_limits_selected_errors():
    """max_count 应该限制代表性异常数量。"""
    lines = [
        "ERROR java.lang.OutOfMemoryError: Java heap space",
        "ERROR database connection refused",
        "ERROR request timeout after 30 seconds",
        "ERROR java.lang.NullPointerException",
    ]

    result = select_representative_errors(
        lines=lines,
        max_count=2,
    )

    assert len(result) == 2
    assert result[0]["severity"] == "P0"
    assert result[1]["severity"] == "P1"


def test_non_error_lines_are_ignored():
    """INFO 和 WARN 日志不应该成为代表性异常。"""
    lines = [
        "INFO application started",
        "WARN memory usage high",
        "INFO health check passed",
    ]

    result = select_representative_errors(lines)

    assert result == []