def classify_error(line: str) -> str:
    """根据 ERROR 日志内容判断异常类型。"""
    lower_line = line.lower()

    if "outofmemoryerror" in lower_line or "oom" in lower_line:
        return "内存溢出"

    if "database" in lower_line and (
        "connection refused" in lower_line
        or "connection failed" in lower_line
    ):
        return "数据库连接失败"

    if "timeout" in lower_line:
        return "超时"

    if "nullpointerexception" in lower_line:
        return "空指针异常"

    return "其他"


def assess_severity(error_type: str) -> str:
    """根据异常类型评估严重等级。"""
    severity_map = {
        "内存溢出": "P0",
        "数据库连接失败": "P1",
        "超时": "P2",
        "空指针异常": "P2",
        "其他": "P3",
    }

    return severity_map.get(error_type, "P3")

def summarize_errors(lines: list[str]) -> dict[str, object]:
    """统计异常类型并找出最高严重等级。"""
    counts = {
        "数据库连接失败": 0,
        "内存溢出": 0,
        "空指针异常": 0,
        "超时": 0,
        "其他": 0,
    }

    severity_order = {
        "P0": 0,
        "P1": 1,
        "P2": 2,
        "P3": 3,
    }

    highest_severity = "P3"

    for line in lines:
        error_type = classify_error(line)
        counts[error_type] += 1

        severity = assess_severity(error_type)

        if severity_order[severity] < severity_order[highest_severity]:
            highest_severity = severity

    return {
        "counts": counts,
        "highest_severity": highest_severity,
    }

def summarize_errors(lines: list[str]) -> dict[str, object]:
    """统计异常类型并找出最高严重等级。"""
    counts = {
        "数据库连接失败": 0,
        "内存溢出": 0,
        "空指针异常": 0,
        "超时": 0,
        "其他": 0,
    }

    severity_order = {
        "P0": 0,
        "P1": 1,
        "P2": 2,
        "P3": 3,
    }

    highest_severity = "P3"

    for line in lines:
        error_type = classify_error(line)
        counts[error_type] += 1

        severity = assess_severity(error_type)

        if severity_order[severity] < severity_order[highest_severity]:
            highest_severity = severity

    return {
        "counts": counts,
        "highest_severity": highest_severity,
    }