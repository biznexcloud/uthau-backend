from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from core.database import get_db
from core.deps import require_role
from models.user import User
from schemas.wallet import WalletResponse, TopupRequest, TransactionResponse
from schemas.common import PaginatedResponse
from crud import wallet as wallet_crud

router = APIRouter(prefix="/customer", tags=["Customer"])


@router.get("/wallet", response_model=WalletResponse)
def get_wallet(db: Session = Depends(get_db), current_user: User = Depends(require_role("customer"))):
    return wallet_crud.get_or_create_wallet(db, current_user.id)


@router.post("/wallet/topup", response_model=WalletResponse)
def topup(body: TopupRequest, db: Session = Depends(get_db), current_user: User = Depends(require_role("customer"))):
    return wallet_crud.topup(db, current_user.id, body.amount)


@router.get("/wallet/transactions", response_model=PaginatedResponse[TransactionResponse])
def transactions(page: int = Query(1, ge=1), size: int = Query(10, ge=1, le=100), db: Session = Depends(get_db), current_user: User = Depends(require_role("customer"))):
    skip = (page - 1) * size
    items, total = wallet_crud.list_transactions(db, current_user.id, skip=skip, limit=size)
    return PaginatedResponse(items=items, total=total, page=page, size=size)
