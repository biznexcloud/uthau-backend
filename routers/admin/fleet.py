from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from core.database import get_db
from core.deps import require_role
from models.user import User as UserModel
from schemas.user import UserResponse
from schemas.common import PaginatedResponse
from crud import user as user_crud

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/fleet/drivers", response_model=PaginatedResponse[UserResponse])
def list_drivers(page: int = Query(1, ge=1), size: int = Query(10, ge=1, le=100), db: Session = Depends(get_db), current_user: UserModel = Depends(require_role("admin"))):
    skip = (page - 1) * size
    items, total = user_crud.list_users(db, role="driver", skip=skip, limit=size)
    return PaginatedResponse(items=items, total=total, page=page, size=size)


@router.get("/fleet/drivers/{driver_id}", response_model=UserResponse)
def get_driver(driver_id: int, db: Session = Depends(get_db), current_user: UserModel = Depends(require_role("admin"))):
    user = user_crud.get_user(db, driver_id)
    if not user or user.role.value != "driver":
        raise HTTPException(status_code=404, detail="Driver not found")
    return user


@router.post("/fleet/drivers/{driver_id}/approve", response_model=UserResponse)
def approve_driver(driver_id: int, db: Session = Depends(get_db), current_user: UserModel = Depends(require_role("admin"))):
    user = user_crud.approve_kyc(db, driver_id)
    if not user:
        raise HTTPException(status_code=404, detail="Driver not found")
    return user


@router.post("/fleet/drivers/{driver_id}/suspend", response_model=UserResponse)
def suspend_driver(driver_id: int, db: Session = Depends(get_db), current_user: UserModel = Depends(require_role("admin"))):
    user = user_crud.update_user(db, driver_id, is_active=False)
    if not user:
        raise HTTPException(status_code=404, detail="Driver not found")
    return user
