from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from core.database import get_db
from core.deps import require_role
from models.user import User as UserModel
from models.wallet import WalletTransaction, Wallet, TxnReference

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/payouts")
def list_payouts(page: int = Query(1, ge=1), size: int = Query(10, ge=1, le=100), db: Session = Depends(get_db), current_user: UserModel = Depends(require_role("admin"))):
    skip = (page - 1) * size
    q = (
        db.query(WalletTransaction)
        .filter(WalletTransaction.reference == TxnReference.WITHDRAW)
        .order_by(desc(WalletTransaction.created_at))
    )
    total = q.count()
    items = q.offset(skip).limit(size).all()
    result = []
    for txn in items:
        wallet = db.query(Wallet).filter(Wallet.id == txn.wallet_id).first()
        driver = db.query(UserModel).filter(UserModel.id == wallet.user_id).first() if wallet else None
        result.append({
            "id": txn.id,
            "driver_id": wallet.user_id if wallet else None,
            "driver_name": driver.name if driver else None,
            "driver_phone": driver.phone if driver else None,
            "amount": txn.amount,
            "status": txn.type.value,
            "requested_at": txn.created_at.isoformat() if txn.created_at else None,
        })
    return {"items": result, "total": total, "page": page, "size": size}
