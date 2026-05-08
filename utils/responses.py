"""
统一响应工具
解决API响应格式不一致的问题
"""
from typing import Any, Optional, List, TypeVar, Generic
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from fastapi import HTTPException


T = TypeVar('T')


class ApiResponse(BaseModel):
    """统一API响应格式"""
    code: int = 200
    message: str = "success"
    data: Optional[Any] = None


class PaginatedData(BaseModel):
    """分页数据格式"""
    total: int = 0
    page: int = 1
    page_size: int = 20
    list: List[Any] = []


class ListDataResponse(ApiResponse):
    """列表响应"""
    data: PaginatedData


def success_response(data: Any = None, message: str = "success") -> dict:
    """成功响应"""
    return {"code": 200, "message": message, "data": data}


def error_response(code: int = 400, message: str = "error", data: Any = None) -> dict:
    """错误响应"""
    return {"code": code, "message": message, "data": data}


def paginated_response(
    items: List[Any], 
    total: int, 
    page: int = 1, 
    page_size: int = 20
) -> dict:
    """分页响应"""
    return {
        "code": 200,
        "message": "success",
        "data": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "list": items
        }
    }


def http_exception(detail: str, status_code: int = 400) -> HTTPException:
    """创建HTTP异常"""
    return HTTPException(status_code=status_code, detail=detail)


def require_role(roles: List[str], current_role: str) -> None:
    """检查用户角色"""
    if current_role not in roles:
        raise http_exception(f"权限不足，需要角色: {', '.join(roles)}", 403)
