from pydantic import BaseModel
from typing import Optional, Any, List

class ResponseBase(BaseModel):
    code: int = 200
    message: str = "success"
    data: Optional[Any] = None

class ListResponse(ResponseBase):
    data: List[Any]
    total: int = 0
