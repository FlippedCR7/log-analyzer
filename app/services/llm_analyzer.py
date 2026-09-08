import json

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.utils.config import (
    API_KEY,
    BASE_URL,
    ENABLE_LLM,
    MAX_LLM_TOKENS,
    MODEL_NAME,
)


def get_llm() -> ChatOpenAI:
    """创建 DeepSeek 大模型客户端。"""
    return ChatOpenAI(
        api_key=API_KEY,
        base_url=BASE_URL,
        model=MODEL_NAME,
        temperature=0.2,
        max_tokens=MAX_LLM_TOKENS,
    )


def build_historical_cases_text(
    historical_cases: list[dict[str, object]],
) -> str:
    """把历史案例整理成适合提供给大模型的文本。"""
    case_texts: list[str] = []

    for index, case in enumerate(historical_cases, start=1):
        case_texts.append(
            f"案例 {index}:\n"
            f"{case.get('content', '')}"
        )

    return "\n\n".join(case_texts)


def build_representative_errors_text(
    representative_errors: list[dict[str, object]],
) -> str:
    """整理代表性异常，不重复附带上下文。"""
    error_texts: list[str] = []

    for index, error in enumerate(representative_errors, start=1):
        error_texts.append(
            f"异常 {index}:\n"
            f"异常类型: {error.get('error_type', '')}\n"
            f"严重等级: {error.get('severity', '')}\n"
            f"异常日志: {error.get('line', '')}"
        )

    return "\n\n".join(error_texts)


def build_merged_context_text(
    representative_errors: list[dict[str, object]],
) -> str:
    """合并所有代表性异常的上下文，并去除重复日志行。"""
    merged_lines: list[str] = []
    seen_lines: set[str] = set()

    for error in representative_errors:
        context = error.get("context", [])

        if not isinstance(context, list):
            continue

        for line in context:
            line_text = str(line)

            if line_text in seen_lines:
                continue

            merged_lines.append(line_text)
            seen_lines.add(line_text)

    return "\n".join(merged_lines)


def analyze_with_llm(
    representative_errors: list[dict[str, object]],
    historical_cases: list[dict[str, object]],
) -> dict[str, object]:
    """使用一次 LLM 调用生成可能根因和处理建议。"""

    if not ENABLE_LLM:
        return {
            "available": False,
            "reason": "LLM disabled",
            "possible_root_cause": "",
            "evidence": [],
            "confidence": "",
            "suggestions": [],
        }

    if not representative_errors:
        return {
            "available": False,
            "reason": "no error logs",
            "possible_root_cause": "",
            "evidence": [],
            "confidence": "",
            "suggestions": [],
        }

    representative_errors_text = build_representative_errors_text(
        representative_errors
    )

    merged_context_text = build_merged_context_text(
        representative_errors
    )

    historical_cases_text = build_historical_cases_text(
        historical_cases
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
你是一名日志故障诊断助手。

你的任务不是断言故障根因，而是根据代表性异常、
去重后的日志上下文和历史案例，
给出谨慎、可解释、可执行的可能根因分析。

要求：

1. 只能根据提供的异常日志、上下文和历史案例进行分析，不要凭空编造事实。
2. 优先结合异常出现顺序、上下文和严重等级判断可能的因果关系。
3. 使用“可能”“疑似”等措辞，不要把推测描述成确定事实。
4. possible_root_cause 使用中文，不超过 200 字。
5. evidence 必须能直接对应输入日志、上下文或历史案例。
6. 不要仅凭单条健康检查、INFO 或 WARN 日志推断系统已经恢复或故障已解决。
7. confidence 只能是：高、中、低。
8. suggestions 给出 2～4 条可执行建议，可包含命令、检查步骤或配置项。
9. 如果现有信息不足以判断因果关系，要明确指出信息不足。
10. 只返回合法 JSON，不要返回 Markdown，不要添加 ```json。

返回格式必须是：

{{
  "possible_root_cause": "可能根因",
  "evidence": [
    "证据1",
    "证据2"
  ],
  "confidence": "高",
  "suggestions": [
    "建议1",
    "建议2"
  ]
}}
""",
            ),
            (
                "human",
                """
代表性异常：

{representative_errors_text}

去重后的日志上下文：

{merged_context_text}

检索到的历史故障案例：

{historical_cases_text}
""",
            ),
        ]
    )

    try:
        llm = get_llm()

        chain = prompt | llm

        response = chain.invoke(
            {
                "representative_errors_text": representative_errors_text,
                "merged_context_text": merged_context_text,
                "historical_cases_text": historical_cases_text,
            }
        )

        result = json.loads(str(response.content))

        return {
            "available": True,
            "reason": "",
            "possible_root_cause": result.get(
                "possible_root_cause",
                "",
            ),
            "evidence": result.get("evidence", []),
            "confidence": result.get("confidence", ""),
            "suggestions": result.get("suggestions", []),
        }

    except Exception as exc:
        return {
            "available": False,
            "reason": f"LLM analysis failed: {type(exc).__name__}",
            "possible_root_cause": "",
            "evidence": [],
            "confidence": "",
            "suggestions": [],
        }