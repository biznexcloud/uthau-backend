from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from core.deps import require_role
from models.user import User
from models.delivery import DeliveryStatus
from schemas.delivery import DeliveryResponse
from schemas.common import PaginatedResponse, MessageResponse
from crud import delivery as delivery_crud

router = APIRouter(prefix="/driver", tags=["Driver"])


@router.get("/orders", response_model=PaginatedResponse[DeliveryResponse])
def available_orders(page: int = 1, size: int = 10, db: Session = Depends(get_db), current_user: User = Depends(require_role("driver"))):
    skip = (page - 1) * size
    items, total = delivery_crud.list_available_deliveries(db, skip=skip, limit=size)
    return PaginatedResponse(items=items, total=total, page=page, size=size)


@router.post("/orders/{order_id}/accept", response_model=DeliveryResponse)
def accept_order(order_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_role("driver"))):
    result = delivery_crud.assign_driver(db, order_id, current_user.id)
    if not result:
        raise HTTPException(status_code=400, detail="Order not available")
    return result


@router.post("/orders/{order_id}/reject", response_model=MessageResponse)
def reject_order(order_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_role("driver"))):
    delivery = delivery_crud.get_delivery(db, order_id)
    if not delivery:
        raise HTTPException(status_code=404, detail="Order not found")
    if delivery.status not in [DeliveryStatus.PENDING, DeliveryStatus.ASSIGNED]:
        raise HTTPException(status_code=400, detail="Cannot reject order at current status")
    if delivery.status == DeliveryStatus.ASSIGNED and delivery.driver_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your assigned order")
    delivery.status = DeliveryStatus.PENDING
    delivery.driver_id = None
    db.commit()
    return {"message": "Order rejected and returned to available pool"}


@router.post("/orders/{order_id}/arrived", response_model=DeliveryResponse)
def arrived_at_pickup(order_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_role("driver"))):
    result = delivery_crud.update_status(db, order_id, "arrived_pickup")
    if not result:
        raise HTTPException(status_code=400, detail="Cannot update")
    return result


@router.post("/orders/{order_id}/start", response_model=DeliveryResponse)
def start_trip(order_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_role("driver"))):
    result = delivery_crud.update_status(db, order_id, "picked_up")
    if not result:
        raise HTTPException(status_code=400, detail="Cannot update")
    return result


@router.post("/orders/{order_id}/complete", response_model=DeliveryResponse)
def complete_delivery(order_id: int, proof_url: str = "", db: Session = Depends(get_db), current_user: User = Depends(require_role("driver"))):
    result = delivery_crud.complete_with_proof(db, order_id, proof_url)
    if not result:
        raise HTTPException(status_code=400, detail="Cannot complete")
    return result


@router.get("/orders/assigned", response_model=PaginatedResponse[DeliveryResponse])
def assigned_orders(page: int = 1, size: int = 10, db: Session = Depends(get_db), current_user: User = Depends(require_role("driver"))):
    skip = (page - 1) * size
    items, total = delivery_crud.list_deliveries(db, user_id=current_user.id, role="driver", skip=skip, limit=size)
    return PaginatedResponse(items=items, total=total, page=page, size=size)
