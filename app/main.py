from fastapi.responses import JSONResponse
from fastapi import FastAPI, File, Request, UploadFile
from app.analyzer import analyze_log
from pathlib import Path
from app.models import ApiResponse
import uuid
from app.utils.logger import get_logger

app = FastAPI()
logger = get_logger(__name__)

@app.exception_handler(Exception)
async def global_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={
            "code": 5000,
            "message": "服务器内部错误",
            "data": None,
        },
    )

@app.get("/", response_model=ApiResponse)
def root() -> ApiResponse:
    return ApiResponse(
        code=0,
        message="success",
        data={
            "status": "log analyzer api is running",
        },
    )
def root() -> dict[str, object]:
    return {
        "code": 0,
        "message": "success",
        "data": {
            "status": "log analyzer api is running"
        },
    }


@app.post("/upload", response_model=ApiResponse)
async def upload_log(
    file: UploadFile = File(...)
) -> ApiResponse | JSONResponse:
    trace_id = str(uuid.uuid4())

    logger.info(
        "upload started",
        extra={"trace_id": trace_id},
    )

    filename = file.filename or ""
    suffix = Path(filename).suffix.lower()

    if suffix not in {".log", ".txt"}:
        return JSONResponse(
            status_code=400,
            content={
                "code": 4001,
                "message": "仅支持 .log 或 .txt 文件",
                "data": None,
            },
        )

    content = await file.read()

    max_size = 10 * 1024 * 1024

    if len(content) > max_size:
        return JSONResponse(
            status_code=400,
            content={
                "code": 4002,
                "message": "文件大小不能超过 10MB",
                "data": None,
            },
        )

    try:
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            return JSONResponse(
                status_code=400,
                content={
                    "code": 4003,
                    "message": "日志文件编码错误，请使用 UTF-8 编码",
                    "data": None,
                },
            )
    except UnicodeDecodeError:
        return JSONResponse(
            status_code=400,
            content={
                "code": 4003,
                "message": "日志文件编码错误，请使用 UTF-8 编码",
                "data": None,
            },
        )
    lines = text.splitlines()

    logger.info(
        "parse completed",
        extra={"trace_id": trace_id},
    )

    result = analyze_log(
        lines=lines,
        trace_id=trace_id,
    )
    logger.info(
        "analysis completed",
        extra={"trace_id": trace_id},
    )
    return ApiResponse(
        code=0,
        message="success",
        data=result,
    )

