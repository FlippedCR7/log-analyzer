from typing import Any

from pydantic import BaseModel


class ApiResponse(BaseModel):
    """统一 API 响应模型。"""

    code: int
    message: str
    data: Any | None = None