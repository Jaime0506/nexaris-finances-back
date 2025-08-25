from typing import Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")

class Response(BaseModel, Generic[T]):
    status: str
    data: T | None = None
    message: str
