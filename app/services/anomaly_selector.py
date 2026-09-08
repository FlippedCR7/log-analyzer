from app.log_classifier import assess_severity, classify_error


def select_representative_errors(
    lines: list[str],
    max_count: int = 3,
) -> list[dict[str, object]]:
    """选择代表性异常，并提取每条异常前后 5 行上下文。"""
    selected: list[dict[str, object]] = []
    seen_types: set[str] = set()

    severity_order = {
        "P0": 0,
        "P1": 1,
        "P2": 2,
        "P3": 3,
    }

    candidates: list[dict[str, object]] = []

    for index, line in enumerate(lines):
        if "ERROR" not in line:
            continue

        error_type = classify_error(line)
        severity = assess_severity(error_type)

        candidates.append(
            {
                "index": index,
                "line": line,
                "error_type": error_type,
                "severity": severity,
            }
        )

    candidates.sort(
        key=lambda item: severity_order.get(
            str(item["severity"]),
            3,
        )
    )

    for candidate in candidates:
        error_type = str(candidate["error_type"])

        if error_type in seen_types:
            continue

        index = int(candidate["index"])

        start = max(0, index - 5)
        end = min(len(lines), index + 6)

        context = lines[start:end]

        selected.append(
            {
                "index": index,
                "line": candidate["line"],
                "error_type": error_type,
                "severity": candidate["severity"],
                "context": context,
            }
        )

        seen_types.add(error_type)

        if len(selected) >= max_count:
            break

    return selected