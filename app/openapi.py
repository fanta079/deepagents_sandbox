from pydantic import BaseModel
from typing import Generic, TypeVar, Optional

T = TypeVar("T")

class APIResponse(BaseModel, Generic[T]):
    code: str = "0"
    message: str = "success"
    data: Optional[T] = None

class PaginatedResponse(BaseModel, Generic[T]):
    code: str = "0"
    message: str = "success"
    data: list[T]
    total: int
    page: int
    page_size: int
