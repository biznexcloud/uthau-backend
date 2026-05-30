from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from core.deps import require_role
from models.user import User as UserModel
from models.delivery import Delivery
from schemas.common import AnalyticsDrivers
from crud import user as user_crud

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/analytics/revenue")
def revenue(db: Session = Depends(get_db), current_user: UserModel = Depends(require_role("admin"))):
    total = db.query(Delivery).filter(Delivery.status == "delivered").count()
    revenue = db.query(Delivery).filter(Delivery.status == "delivered").with_entities(Delivery.total_fare).all()
    total_revenue = sum(r[0] for r in revenue) if revenue else 0
    return {"total_orders": total, "total_revenue": round(total_revenue, 2), "currency": "NPR"}


@router.get("/analytics/orders")
def order_stats(db: Session = Depends(get_db), current_user: UserModel = Depends(require_role("admin"))):
    total = db.query(Delivery).count()
    active = db.query(Delivery).filter(Delivery.status.in_(["pending", "assigned", "picked_up", "in_transit"])).count()
    completed = db.query(Delivery).filter(Delivery.status == "delivered").count()
    cancelled = db.query(Delivery).filter(Delivery.status == "cancelled").count()
    return {"total": total, "active": active, "completed": completed, "cancelled": cancelled}


@router.get("/analytics/drivers")
def driver_stats(db: Session = Depends(get_db), current_user: UserModel = Depends(require_role("admin"))):
    from models.user import User, UserRole
    total = db.query(User).filter(User.role == UserRole.DRIVER).count()
    online = db.query(User).filter(User.role == UserRole.DRIVER, User.is_online == True).count()
    kyc_pending = db.query(User).filter(User.role == UserRole.DRIVER, User.is_kyc_verified == False).count()
    return AnalyticsDrivers(total_drivers=total, online=online, on_trip=0, offline=total - online, kyc_pending=kyc_pending)
