from pydantic import BaseModel
from typing import Generic, List, TypeVar

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    size: int


class MessageResponse(BaseModel):
    message: str
    status: str = "ok"


class AnalyticsDrivers(BaseModel):
    total_drivers: int
    online: int
    on_trip: int
    offline: int
    kyc_pending: int
