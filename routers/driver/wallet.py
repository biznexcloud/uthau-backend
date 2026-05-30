from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from core.deps import require_role
from models.user import User
from schemas.wallet import WalletResponse, WithdrawRequest, TransactionResponse
from schemas.common import PaginatedResponse
from crud import wallet as wallet_crud

router = APIRouter(prefix="/driver", tags=["Driver"])


@router.get("/wallet", response_model=WalletResponse)
def get_wallet(db: Session = Depends(get_db), current_user: User = Depends(require_role("driver"))):
    return wallet_crud.get_or_create_wallet(db, current_user.id, wallet_type="driver")


@router.post("/wallet/withdraw", response_model=WalletResponse)
def withdraw(body: WithdrawRequest, db: Session = Depends(get_db), current_user: User = Depends(require_role("driver"))):
    try:
        return wallet_crud.withdraw(db, current_user.id, body.amount)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/wallet/transactions", response_model=PaginatedResponse[TransactionResponse])
def transactions(page: int = 1, size: int = 10, db: Session = Depends(get_db), current_user: User = Depends(require_role("driver"))):
    skip = (page - 1) * size
    items, total = wallet_crud.list_transactions(db, current_user.id, skip=skip, limit=size)
    return PaginatedResponse(items=items, total=total, page=page, size=size)
