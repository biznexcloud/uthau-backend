from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from models.delivery import GoodsType, PaymentMethod


class DeliveryCreate(BaseModel):
    pickup_address: str
    pickup_lat: Optional[float] = None
    pickup_lng: Optional[float] = None
    dropoff_address: str
    dropoff_lat: Optional[float] = None
    dropoff_lng: Optional[float] = None
    vehicle_type_id: int
    goods_type: Optional[GoodsType] = None
    description: Optional[str] = None
    payment_method: PaymentMethod = PaymentMethod.CASH
    scheduled_at: Optional[str] = None


class DeliveryResponse(BaseModel):
    id: int
    crn: Optional[str] = None
    customer_id: int
    driver_id: Optional[int] = None
    pickup_address: str
    pickup_lat: Optional[float] = None
    pickup_lng: Optional[float] = None
    dropoff_address: str
    dropoff_lat: Optional[float] = None
    dropoff_lng: Optional[float] = None
    vehicle_type_id: Optional[int] = None
    goods_type: Optional[GoodsType] = None
    description: Optional[str] = None
    status: str
    distance_km: float
    duration_min: float = 0
    base_fare: float = 0
    surge_multiplier: float = 1.0
    total_fare: float
    net_earnings: float = 0
    commission_percent: float = 20.0
    payment_method: str
    payment_status: str
    proof_photo_url: Optional[str] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class DeliveryAssign(BaseModel):
    driver_id: int


class FareEstimateRequest(BaseModel):
    pickup_lat: float
    pickup_lng: float
    dropoff_lat: float
    dropoff_lng: float
    vehicle_type_id: int


class FareEstimateResponse(BaseModel):
    distance_km: float
    duration_min: float
    base_fare: float
    distance_charge: float
    time_charge: float
    surge_multiplier: float
    total_fare: float
