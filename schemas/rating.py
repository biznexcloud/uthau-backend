from pydantic import BaseModel
from typing import Optional


class RatingCreate(BaseModel):
    delivery_id: int
    to_user_id: int
    score: float
    review: Optional[str] = None


class RatingResponse(BaseModel):
    id: int
    delivery_id: int
    from_user_id: int
    to_user_id: int
    score: float
    review: Optional[str] = None

    model_config = {"from_attributes": True}
