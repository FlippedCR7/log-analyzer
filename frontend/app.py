import html
from pathlib import Path

import gradio as gr
import requests


BACKEND_URL = "http://127.0.0.1:8000/upload"


def severity_badge(severity: str) -> str:
    """返回严重等级徽标 HTML。"""
    level_map = {
        "P0": "🔴 P0",
        "P1": "🟠 P1",
        "P2": "🟡 P2",
        "P3": "🟢 P3",
    }
    return level_map.get(severity, severity)


def build_error_html(
    representative_errors: list[dict[str, object]],
) -> str:
    """把代表性异常转换成 HTML 卡片。"""
    if not representative_errors:
        return "<p>未发现代表性异常。</p>"

    cards: list[str] = []

    for error in representative_errors:
        severity = html.escape(str(error.get("severity", "")))
        error_type = html.escape(str(error.get("error_type", "")))
        line = html.escape(str(error.get("line", "")))

        cards.append(
            f"""
            <div style="
                border: 1px solid #444;
                border-radius: 10px;
                padding: 14px;
                margin-bottom: 10px;
            ">
                <div style="font-size: 18px; font-weight: bold;">
                    {severity_badge(severity)} · {error_type}
                </div>

                <div style="
                    margin-top: 8px;
                    font-family: monospace;
                    white-space: pre-wrap;
                ">
                    {line}
                </div>
            </div>
            """
        )

    return "".join(cards)


def build_cases_html(
    historical_cases: list[dict[str, object]],
) -> str:
    """把历史案例转换成 HTML 卡片。"""
    if not historical_cases:
        return "<p>暂无相似历史案例。</p>"

    cards: list[str] = []

    for index, case in enumerate(historical_cases, start=1):
        title = html.escape(str(case.get("title", "")))
        error_type = html.escape(str(case.get("error_type", "")))
        severity = html.escape(str(case.get("severity", "")))
        content = html.escape(str(case.get("content", "")))

        cards.append(
            f"""
            <details style="
                border: 1px solid #444;
                border-radius: 10px;
                padding: 12px;
                margin-bottom: 10px;
            ">
                <summary style="
                    cursor: pointer;
                    font-size: 17px;
                    font-weight: bold;
                ">
                    Top {index} · {title} · {severity_badge(severity)}
                </summary>

                <div style="margin-top: 10px;">
                    <b>异常类型：</b>{error_type}
                </div>

                <pre style="
                    white-space: pre-wrap;
                    margin-top: 10px;
                    font-family: monospace;
                ">{content}</pre>
            </details>
            """
        )

    return "".join(cards)


def build_llm_html(
    llm_analysis: dict[str, object],
) -> str:
    """把 LLM 分析结果转换成诊断报告 HTML。"""
    available = bool(llm_analysis.get("available", False))

    if not available:
        reason = html.escape(str(llm_analysis.get("reason", "")))

        if reason == "LLM disabled":
            return """
            <div style="
                border: 1px solid #555;
                border-radius: 10px;
                padding: 16px;
            ">
                <b>AI 分析当前已关闭。</b>
                <p>当前仅展示本地解析、分类和 RAG 检索结果。</p>
            </div>
            """

        return f"""
        <div style="
            border: 1px solid #555;
            border-radius: 10px;
            padding: 16px;
        ">
            <b>AI 分析暂不可用</b>
            <p>{reason}</p>
        </div>
        """

    root_cause = html.escape(
        str(llm_analysis.get("possible_root_cause", ""))
    )
    confidence = html.escape(
        str(llm_analysis.get("confidence", ""))
    )

    evidence = llm_analysis.get("evidence", [])
    suggestions = llm_analysis.get("suggestions", [])

    evidence_items = ""

    if isinstance(evidence, list):
        evidence_items = "".join(
            f"<li>{html.escape(str(item))}</li>"
            for item in evidence
        )

    suggestion_items = ""

    if isinstance(suggestions, list):
        suggestion_items = "".join(
            f"<li>{html.escape(str(item))}</li>"
            for item in suggestions
        )

    return f"""
    <div style="
        border: 1px solid #444;
        border-radius: 12px;
        padding: 18px;
    ">
        <h3>可能根因</h3>
        <p>{root_cause}</p>

        <h3>置信度</h3>
        <p><b>{confidence}</b></p>

        <h3>证据</h3>
        <ul>
            {evidence_items}
        </ul>

        <h3>处理建议</h3>
        <ol>
            {suggestion_items}
        </ol>
    </div>
    """


def build_error_response(
    message: str,
) -> tuple[str, str, str, str, str, str]:
    """生成统一的前端错误展示。"""
    safe_message = html.escape(message)

    return (
        "0",
        "0",
        "0",
        "0",
        "分析失败",
        f"<p>{safe_message}</p>",
    )


def analyze_file(
    file_path: str | None,
) -> tuple[str, str, str, str, str, str]:
    """通过 FastAPI 上传日志，并展示诊断结果。"""
    if not file_path:
        return (
            "0",
            "0",
            "0",
            "0",
            "未分析",
            "<p>请先上传日志文件。</p>",
        )

    path = Path(file_path)

    if path.suffix.lower() not in {".log", ".txt"}:
        return build_error_response(
            "仅支持 .log 或 .txt 文件。"
        )

    try:
        with path.open("rb") as file:
            response = requests.post(
                BACKEND_URL,
                files={
                    "file": (
                        path.name,
                        file,
                        "text/plain",
                    )
                },
                timeout=120,
            )
    except requests.ConnectionError:
        return build_error_response(
            "无法连接 FastAPI 后端，请确认后端已启动。"
        )
    except requests.Timeout:
        return build_error_response(
            "后端分析超时，请稍后重试。"
        )
    except requests.RequestException as exc:
        return build_error_response(
            f"请求后端失败：{type(exc).__name__}"
        )

    try:
        payload = response.json()
    except ValueError:
        return build_error_response(
            "后端返回了无法解析的响应。"
        )

    if response.status_code != 200:
        message = str(
            payload.get(
                "message",
                f"后端请求失败，HTTP {response.status_code}",
            )
        )
        return build_error_response(message)

    if payload.get("code") != 0:
        return build_error_response(
            str(payload.get("message", "分析失败"))
        )

    result = payload.get("data")

    if not isinstance(result, dict):
        return build_error_response(
            "后端返回的数据格式不正确。"
        )

    parse_result = result.get("parse_result", {})
    error_summary = result.get("error_summary", {})
    representative_errors = result.get(
        "representative_errors",
        [],
    )
    historical_cases = result.get(
        "historical_cases",
        [],
    )
    llm_analysis = result.get(
        "llm_analysis",
        {},
    )

    level_counts = parse_result.get("level_counts", {})

    total = str(parse_result.get("total", 0))
    info_count = str(level_counts.get("INFO", 0))
    warn_count = str(level_counts.get("WARN", 0))
    error_count = str(level_counts.get("ERROR", 0))

    highest_severity = str(
        error_summary.get(
            "highest_severity",
            "P3",
        )
    )

    errors_html = build_error_html(
        representative_errors
        if isinstance(representative_errors, list)
        else []
    )

    cases_html = build_cases_html(
        historical_cases
        if isinstance(historical_cases, list)
        else []
    )

    llm_html = build_llm_html(
        llm_analysis
        if isinstance(llm_analysis, dict)
        else {}
    )

    full_report = f"""
    <h2>代表性异常</h2>
    {errors_html}

    <h2 style="margin-top: 24px;">AI 可能根因分析</h2>
    {llm_html}

    <h2 style="margin-top: 24px;">Top 3 相似历史案例</h2>
    {cases_html}
    """

    return (
        total,
        info_count,
        warn_count,
        error_count,
        severity_badge(highest_severity),
        full_report,
    )


with gr.Blocks(
    title="智能日志异常诊断系统",
) as demo:

    gr.Markdown(
        """
# 智能日志异常诊断系统

上传 `.log` 或 `.txt` 日志文件，系统会自动完成日志解析、
异常分类、严重等级判断、历史案例检索和 AI 可能根因分析。
"""
    )

    file_input = gr.File(
        label="上传日志文件",
        file_types=[".log", ".txt"],
        type="filepath",
    )

    analyze_button = gr.Button(
        "开始分析",
        variant="primary",
    )

    gr.Markdown("## 分析概览")

    with gr.Row():
        total_output = gr.Textbox(
            label="总日志数",
            interactive=False,
        )

        info_output = gr.Textbox(
            label="INFO",
            interactive=False,
        )

        warn_output = gr.Textbox(
            label="WARN",
            interactive=False,
        )

        error_output = gr.Textbox(
            label="ERROR",
            interactive=False,
        )

        severity_output = gr.Textbox(
            label="最高严重等级",
            interactive=False,
        )

    gr.Markdown("## 诊断报告")

    report_output = gr.HTML()

    analyze_button.click(
        fn=analyze_file,
        inputs=file_input,
        outputs=[
            total_output,
            info_output,
            warn_output,
            error_output,
            severity_output,
            report_output,
        ],
    )


if __name__ == "__main__":
    demo.launch()