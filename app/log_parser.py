import re
def count_error_lines(lines: list[str]) -> int:
    """统计日志中 ERROR 行的数量。"""
    return sum(1 for line in lines if "ERROR" in line)

def detect_log_level(line: str) -> str:
    """识别单行日志的日志级别。"""
    if "ERROR" in line:
        return "ERROR"
    if "WARN" in line:
        return "WARN"
    if "INFO" in line:
        return "INFO"
    return "UNKNOWN"

def count_log_levels(lines: list[str]) -> dict[str, int]:
    """统计各日志级别的数量。"""
    counts = {
        "INFO": 0,
        "WARN": 0,
        "ERROR": 0,
        "UNKNOWN": 0,
    }

    for line in lines:
        level = detect_log_level(line)
        counts[level] += 1

    return counts

def extract_timestamp(line: str) -> str | None:
    """从日志行中提取时间戳，未找到时返回 None。"""
    pattern = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}"
    match = re.search(pattern, line)

    if match:
        return match.group()

    return None

def parse_log(lines: list[str]) -> dict[str, object]:
    """解析日志并返回基础统计结果。"""
    level_counts = count_log_levels(lines)

    return {
        "total": len(lines),
        "level_counts": level_counts,
    }

def parse_log(lines: list[str]) -> dict[str, object]:
    """解析日志并返回基础统计结果。"""
    level_counts = count_log_levels(lines)
    total = len(lines)

    if total == 0:
        level_ratios = {
            "INFO": 0.0,
            "WARN": 0.0,
            "ERROR": 0.0,
            "UNKNOWN": 0.0,
        }
    else:
        level_ratios = {
            level: count / total
            for level, count in level_counts.items()
        }

    timestamps = []

    for line in lines:
        timestamp = extract_timestamp(line)
        if timestamp is not None:
            timestamps.append(timestamp)

    error_lines = []

    for line in lines:
        if detect_log_level(line) == "ERROR":
            error_lines.append(line)

        if len(error_lines) == 10:
            break

    return {
        "total": total,
        "level_counts": level_counts,
        "level_ratios": level_ratios,
        "timestamps": timestamps,
        "error_lines": error_lines,
    }