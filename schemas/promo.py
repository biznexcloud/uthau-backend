from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PromoCreate(BaseModel):
    code: str
    type: str = "percent"
    value: float
    min_trip_value: float = 0
    max_discount: Optional[float] = None
    usage_limit: int = 100
    expires_at: Optional[str] = None


class PromoResponse(BaseModel):
    id: int
    code: str
    type: str
    value: float
    min_trip_value: float
    max_discount: Optional[float] = None
    usage_limit: int
    used_count: int
    expires_at: Optional[datetime] = None
    is_active: bool

    model_config = {"from_attributes": True}
