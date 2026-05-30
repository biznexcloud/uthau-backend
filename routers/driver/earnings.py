from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from core.database import get_db
from core.deps import require_role
from models.user import User
from crud import delivery as delivery_crud

router = APIRouter(prefix="/driver", tags=["Driver"])


@router.get("/earnings")
def earnings(
    period: str = Query("weekly"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("driver")),
):
    items, total = delivery_crud.list_deliveries(db, user_id=current_user.id, role="driver", status="delivered")
    total_earned = sum(d.net_earnings for d in items)
    return {
        "period": period,
        "total_deliveries": total,
        "total_earned": total_earned,
        "commission_deducted": sum(d.total_fare - d.net_earnings for d in items),
    }
