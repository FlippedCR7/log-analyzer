import html
from pathlib import Path

import gradio as gr

from app.analyzer import analyze_log


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


def analyze_file(
    file_path: str | None,
) -> tuple[str, str, str, str, str, str]:
    """读取日志并返回适合前端展示的诊断结果。"""
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
        return (
            "0",
            "0",
            "0",
            "0",
            "文件错误",
            "<p>仅支持 .log 或 .txt 文件。</p>",
        )

    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return (
            "0",
            "0",
            "0",
            "0",
            "编码错误",
            "<p>文件不是 UTF-8 编码，暂时无法读取。</p>",
        )

    lines = content.splitlines()

    result = analyze_log(
        lines=lines,
        trace_id="gradio-local",
    )

    parse_result = result["parse_result"]
    error_summary = result["error_summary"]
    representative_errors = result["representative_errors"]
    historical_cases = result["historical_cases"]
    llm_analysis = result["llm_analysis"]

    total = str(parse_result["total"])
    info_count = str(parse_result["level_counts"]["INFO"])
    warn_count = str(parse_result["level_counts"]["WARN"])
    error_count = str(parse_result["level_counts"]["ERROR"])

    highest_severity = str(
        error_summary["highest_severity"]
    )

    errors_html = build_error_html(
        representative_errors
    )

    cases_html = build_cases_html(
        historical_cases
    )

    llm_html = build_llm_html(
        llm_analysis
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