from app.log_parser import (
    count_error_lines,
    count_log_levels,
    detect_log_level,
    extract_timestamp,
    parse_log,
)

def test_count_error_lines() -> None:
    lines = [
        "INFO app started",
        "ERROR database failed",
        "WARN retrying",
        "ERROR timeout",
    ]

    result = count_error_lines(lines)

    assert result == 2

def test_detect_error_level() -> None:
    line = "2026-09-04 10:03:45 ERROR database connection failed"
    assert detect_log_level(line) == "ERROR"


def test_detect_warn_level() -> None:
    line = "2026-09-04 10:02:15 WARN connection is slow"
    assert detect_log_level(line) == "WARN"


def test_detect_unknown_level() -> None:
    line = "application started successfully"
    assert detect_log_level(line) == "UNKNOWN"

def test_count_log_levels() -> None:
    lines = [
        "INFO app started",
        "WARN connection slow",
        "ERROR database failed",
        "ERROR timeout",
    ]

    result = count_log_levels(lines)

    assert result["INFO"] == 1
    assert result["WARN"] == 1
    assert result["ERROR"] == 2
    assert result["UNKNOWN"] == 0


def test_count_log_levels_with_unknown() -> None:
    lines = [
        "INFO app started",
        "this is not a standard log line",
    ]

    result = count_log_levels(lines)

    assert result["INFO"] == 1
    assert result["UNKNOWN"] == 1


def test_count_log_levels_empty() -> None:
    result = count_log_levels([])

    assert result == {
        "INFO": 0,
        "WARN": 0,
        "ERROR": 0,
        "UNKNOWN": 0,
    }

def test_extract_timestamp() -> None:
    line = "2026-09-04 10:03:45 ERROR database connection failed"

    result = extract_timestamp(line)

    assert result == "2026-09-04 10:03:45"


def test_extract_timestamp_without_timestamp() -> None:
    line = "ERROR database connection failed"

    result = extract_timestamp(line)

    assert result is None


def test_extract_timestamp_in_middle() -> None:
    line = "[server] 2026-09-04 10:03:45 WARN connection slow"

    result = extract_timestamp(line)

    assert result == "2026-09-04 10:03:45"

def test_parse_log_basic() -> None:
    lines = [
        "INFO app started",
        "WARN connection slow",
        "ERROR database failed",
        "ERROR timeout",
    ]

    result = parse_log(lines)

    assert result["total"] == 4
    assert result["level_counts"]["INFO"] == 1
    assert result["level_counts"]["WARN"] == 1
    assert result["level_counts"]["ERROR"] == 2

def test_parse_log_ratios() -> None:
    lines = [
        "INFO app started",
        "WARN connection slow",
        "ERROR database failed",
        "ERROR timeout",
    ]

    result = parse_log(lines)

    assert result["level_ratios"]["INFO"] == 0.25
    assert result["level_ratios"]["WARN"] == 0.25
    assert result["level_ratios"]["ERROR"] == 0.5
    assert result["level_ratios"]["UNKNOWN"] == 0.0


def test_parse_log_empty_ratios() -> None:
    result = parse_log([])

    assert result["total"] == 0
    assert result["level_ratios"]["INFO"] == 0.0
    assert result["level_ratios"]["ERROR"] == 0.0

def test_parse_log_timestamps() -> None:
    lines = [
        "2026-09-04 10:00:00 INFO app started",
        "2026-09-04 10:01:00 ERROR database failed",
        "WARN no timestamp",
    ]

    result = parse_log(lines)

    assert result["timestamps"] == [
        "2026-09-04 10:00:00",
        "2026-09-04 10:01:00",
    ]


def test_parse_log_without_timestamps() -> None:
    lines = [
        "INFO app started",
        "ERROR database failed",
    ]

    result = parse_log(lines)

    assert result["timestamps"] == []

def test_parse_log_error_lines() -> None:
    lines = [
        "INFO app started",
        "ERROR database failed",
        "WARN retrying",
        "ERROR timeout",
    ]

    result = parse_log(lines)

    assert result["error_lines"] == [
        "ERROR database failed",
        "ERROR timeout",
    ]


def test_parse_log_only_keeps_first_ten_errors() -> None:
    lines = [f"ERROR problem {i}" for i in range(15)]

    result = parse_log(lines)

    assert len(result["error_lines"]) == 10
    assert result["error_lines"][0] == "ERROR problem 0"
    assert result["error_lines"][-1] == "ERROR problem 9"