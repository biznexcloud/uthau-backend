from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from core.deps import get_current_user, require_role
from models.user import User
from schemas.delivery import DeliveryCreate, DeliveryResponse, FareEstimateRequest, FareEstimateResponse
from schemas.common import PaginatedResponse
from crud import delivery as delivery_crud
from services.pricing import calculate_fare
from utils.geo import haversine_km

router = APIRouter(prefix="/customer", tags=["Customer"])


@router.post("/fare-estimate", response_model=FareEstimateResponse)
def fare_estimate(body: FareEstimateRequest, db: Session = Depends(get_db)):
    distance_km = haversine_km(body.pickup_lat, body.pickup_lng, body.dropoff_lat, body.dropoff_lng)
    duration_min = round(distance_km * 2, 1)
    fare = calculate_fare(vehicle_id=body.vehicle_type_id, distance_km=distance_km, duration_min=duration_min, db=db)
    return FareEstimateResponse(**fare)


@router.post("/deliveries", response_model=DeliveryResponse)
def create_delivery(body: DeliveryCreate, db: Session = Depends(get_db), current_user: User = Depends(require_role("customer"))):
    delivery = delivery_crud.create_delivery(db, customer_id=current_user.id, data=body.model_dump())
    return delivery


@router.get("/deliveries", response_model=PaginatedResponse[DeliveryResponse])
def list_deliveries(
    page: int = Query(1, ge=1), size: int = Query(10, ge=1, le=100),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("customer")),
):
    skip = (page - 1) * size
    items, total = delivery_crud.list_deliveries(db, user_id=current_user.id, role="customer", status=status, skip=skip, limit=size)
    return PaginatedResponse(items=items, total=total, page=page, size=size)


@router.get("/deliveries/{delivery_id}", response_model=DeliveryResponse)
def get_delivery(delivery_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_role("customer"))):
    delivery = delivery_crud.get_delivery(db, delivery_id)
    if not delivery or delivery.customer_id != current_user.id:
        raise HTTPException(status_code=404, detail="Delivery not found")
    return delivery


@router.post("/deliveries/{delivery_id}/cancel", response_model=DeliveryResponse)
def cancel_delivery(delivery_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_role("customer"))):
    delivery = delivery_crud.get_delivery(db, delivery_id)
    if not delivery or delivery.customer_id != current_user.id:
        raise HTTPException(status_code=404, detail="Delivery not found")
    result = delivery_crud.cancel_delivery(db, delivery_id)
    if not result:
        raise HTTPException(status_code=400, detail="Cannot cancel at current status")
    return result
