from pydantic import BaseModel
from typing import Optional, Any, Dict, List

class ErrorResponse(BaseModel):
    status: str = "error"
    msg: str

class SuccessResponse(BaseModel):
    status: str = "success"
    msg: str
    data: Optional[Any] = None

class PaginatedResponse(BaseModel):
    status: str = "success"
    msg: str = "Data retrieved successfully"
    data: List[Any]
    total: int
    page: int
    per_page: int
    total_pages: int 