from pydantic import BaseModel
from typing import Optional


class VehicleTypeResponse(BaseModel):
    id: int
    name: str
    capacity_kg: float
    image_url: Optional[str] = None
    base_fare: float
    per_km_rate: float
    per_min_rate: float
    min_fare: float

    model_config = {"from_attributes": True}


class VehicleTypeUpdate(BaseModel):
    base_fare: Optional[float] = None
    per_km_rate: Optional[float] = None
    per_min_rate: Optional[float] = None
    min_fare: Optional[float] = None
    is_active: Optional[int] = None
