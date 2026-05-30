from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from core.database import get_db
from core.deps import require_role
from models.user import User as UserModel
from schemas.promo import PromoCreate, PromoResponse
from schemas.common import PaginatedResponse
from crud import promo as promo_crud

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post("/promos", response_model=PromoResponse)
def create_promo(body: PromoCreate, db: Session = Depends(get_db), current_user: UserModel = Depends(require_role("admin"))):
    return promo_crud.create_promo(db, **body.model_dump())


@router.get("/promos", response_model=PaginatedResponse[PromoResponse])
def list_promos(page: int = Query(1, ge=1), size: int = Query(10, ge=1, le=100), db: Session = Depends(get_db), current_user: UserModel = Depends(require_role("admin"))):
    skip = (page - 1) * size
    items, total = promo_crud.list_promos(db, skip=skip, limit=size)
    return PaginatedResponse(items=items, total=total, page=page, size=size)
