from pydantic import BaseModel
from typing import Optional


class AddressCreate(BaseModel):
    label: str = "other"
    address: str
    lat: Optional[float] = None
    lng: Optional[float] = None
    is_default: bool = False


class AddressResponse(AddressCreate):
    id: int
    user_id: int

    model_config = {"from_attributes": True}
