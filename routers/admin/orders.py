from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from core.database import get_db
from core.deps import require_role
from models.user import User as UserModel
from schemas.delivery import DeliveryResponse, DeliveryAssign
from schemas.common import PaginatedResponse, MessageResponse
from crud import delivery as delivery_crud, payment as payment_crud

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/orders", response_model=PaginatedResponse[DeliveryResponse])
def list_orders(
    page: int = Query(1, ge=1), size: int = Query(10, ge=1, le=100),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db), current_user: UserModel = Depends(require_role("admin")),
):
    skip = (page - 1) * size
    items, total = delivery_crud.list_deliveries(db, status=status, skip=skip, limit=size)
    return PaginatedResponse(items=items, total=total, page=page, size=size)


@router.post("/orders/{order_id}/assign", response_model=DeliveryResponse)
def assign_order(order_id: int, body: DeliveryAssign, db: Session = Depends(get_db), current_user: UserModel = Depends(require_role("admin"))):
    result = delivery_crud.assign_driver(db, order_id, body.driver_id)
    if not result:
        raise HTTPException(status_code=400, detail="Cannot assign")
    return result


@router.post("/orders/{order_id}/cancel", response_model=DeliveryResponse)
def cancel_order(order_id: int, db: Session = Depends(get_db), current_user: UserModel = Depends(require_role("admin"))):
    result = delivery_crud.cancel_delivery(db, order_id)
    if not result:
        raise HTTPException(status_code=400, detail="Cannot cancel")
    return result


@router.post("/orders/{order_id}/refund", response_model=MessageResponse)
def refund_order(order_id: int, db: Session = Depends(get_db), current_user: UserModel = Depends(require_role("admin"))):
    payment_crud.refund_payment(db, order_id)
    return {"message": "Refund processed"}
