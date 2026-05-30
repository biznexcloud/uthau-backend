from pydantic import BaseModel
from typing import Optional, Any, Literal


class WSMessage(BaseModel):
    action: str
    data: dict = {}


class WSResponse(BaseModel):
    action: str
    data: Optional[Any] = None
    status: Literal["ok", "error"] = "ok"
    message: Optional[str] = None


class WSDriverAccept(BaseModel):
    delivery_id: int
    driver_id: Optional[int] = None


class WSDriverUpdateStatus(BaseModel):
    delivery_id: int
    status: str


class WSDriverToggleOnline(BaseModel):
    driver_id: Optional[int] = None
    online: bool = True


class WSCustomerTrackDelivery(BaseModel):
    delivery_id: int


class WSCustomerFareEstimate(BaseModel):
    vehicle_type_id: int
    distance_km: float = 5
    duration_min: float = 10
