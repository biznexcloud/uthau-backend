from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class WalletResponse(BaseModel):
    id: int
    user_id: int
    balance: float
    type: str

    model_config = {"from_attributes": True}


class TopupRequest(BaseModel):
    amount: float
    method: str = "esewa"


class WithdrawRequest(BaseModel):
    amount: float
    method: str = "bank"


class TransactionResponse(BaseModel):
    id: int
    amount: float
    type: str
    reference: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
