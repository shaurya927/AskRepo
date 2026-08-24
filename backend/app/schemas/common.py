from pydantic import BaseModel
from typing import Generic, TypeVar

T = TypeVar('T')

class StatusResponse(BaseModel):
    status: str
    message: str | None = None

class ErrorResponse(BaseModel):
    detail: str

class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    size: int
