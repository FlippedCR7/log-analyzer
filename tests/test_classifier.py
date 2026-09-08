from app.log_classifier import (
    assess_severity,
    classify_error,
    summarize_errors,
)

def test_classify_database_error() -> None:
    line = "ERROR database connection refused"
    assert classify_error(line) == "数据库连接失败"


def test_classify_oom_error() -> None:
    line = "ERROR java.lang.OutOfMemoryError: Java heap space"
    assert classify_error(line) == "内存溢出"


def test_classify_timeout_error() -> None:
    line = "ERROR request timeout after 30 seconds"
    assert classify_error(line) == "超时"


def test_assess_oom_severity() -> None:
    assert assess_severity("内存溢出") == "P0"


def test_assess_database_severity() -> None:
    assert assess_severity("数据库连接失败") == "P1"


def test_assess_other_severity() -> None:
    assert assess_severity("其他") == "P3"

def test_summarize_errors() -> None:
    lines = [
        "ERROR java.lang.OutOfMemoryError: Java heap space",
        "ERROR database connection refused",
        "ERROR request timeout after 30 seconds",
        "ERROR request timeout after 10 seconds",
        "ERROR unknown problem",
    ]

    result = summarize_errors(lines)

    assert result["counts"]["内存溢出"] == 1
    assert result["counts"]["数据库连接失败"] == 1
    assert result["counts"]["超时"] == 2
    assert result["counts"]["其他"] == 1
    assert result["highest_severity"] == "P0"

def test_summarize_errors() -> None:
    lines = [
        "ERROR java.lang.OutOfMemoryError: Java heap space",
        "ERROR database connection refused",
        "ERROR request timeout after 30 seconds",
        "ERROR request timeout after 10 seconds",
        "ERROR unknown problem",
    ]

    result = summarize_errors(lines)

    assert result["counts"]["内存溢出"] == 1
    assert result["counts"]["数据库连接失败"] == 1
    assert result["counts"]["超时"] == 2
    assert result["counts"]["其他"] == 1
    assert result["highest_severity"] == "P0"

def test_classify_null_pointer_error() -> None:
    line = "ERROR java.lang.NullPointerException"
    assert classify_error(line) == "空指针异常"


def test_classify_other_error() -> None:
    line = "ERROR disk space is full"
    assert classify_error(line) == "其他"


def test_assess_timeout_severity() -> None:
    assert assess_severity("超时") == "P2"


def test_assess_null_pointer_severity() -> None:
    assert assess_severity("空指针异常") == "P2"


def test_summarize_errors_without_p0() -> None:
    lines = [
        "ERROR database connection refused",
        "ERROR request timeout after 30 seconds",
    ]

    result = summarize_errors(lines)

    assert result["counts"]["数据库连接失败"] == 1
    assert result["counts"]["超时"] == 1
    assert result["highest_severity"] == "P1"


def test_summarize_errors_empty() -> None:
    result = summarize_errors([])

    assert result["counts"] == {
        "数据库连接失败": 0,
        "内存溢出": 0,
        "空指针异常": 0,
        "超时": 0,
        "其他": 0,
    }
    assert result["highest_severity"] == "P3"