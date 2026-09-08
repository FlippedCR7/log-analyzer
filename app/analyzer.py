from app.log_classifier import summarize_errors
from app.log_parser import parse_log
from app.services.anomaly_selector import select_representative_errors
from app.services.llm_analyzer import analyze_with_llm
from app.services.rag_engine import retrieve_similar_cases
from app.utils.logger import get_logger


logger = get_logger(__name__)


def analyze_log(
    lines: list[str],
    trace_id: str = "",
) -> dict[str, object]:
    """整合日志解析、异常分类、代表性异常、RAG 和 LLM 分析结果。"""
    parse_result = parse_log(lines)

    error_lines = parse_result["error_lines"]
    error_summary = summarize_errors(error_lines)

    representative_errors = select_representative_errors(
        lines=lines,
        max_count=3,
    )

    historical_cases: list[dict[str, object]] = []
    seen_ids: set[str] = set()

    for error in representative_errors:
        error_line = str(error["line"])

        similar_cases = retrieve_similar_cases(
            query=error_line,
            k=1,
        )

        for case in similar_cases:
            case_id = str(case.get("id", ""))

            if case_id not in seen_ids:
                historical_cases.append(case)
                seen_ids.add(case_id)

    historical_cases = historical_cases[:3]

    logger.info(
        "retrieval completed",
        extra={"trace_id": trace_id},
    )

    llm_analysis = analyze_with_llm(
        representative_errors=representative_errors,
        historical_cases=historical_cases,
    )

    logger.info(
        "generation completed",
        extra={"trace_id": trace_id},
    )

    return {
        "parse_result": parse_result,
        "error_summary": error_summary,
        "representative_errors": representative_errors,
        "historical_cases": historical_cases,
        "llm_analysis": llm_analysis,
    }