from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PaymentResponse(BaseModel):
    id: int
    delivery_id: Optional[int] = None
    amount: float
    method: str
    status: str
    gateway_ref: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
