from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from core.deps import require_role
from models.user import User
from schemas.user import UserResponse, UserUpdate
from crud import user as user_crud, rating as rating_crud

router = APIRouter(prefix="/driver", tags=["Driver"])


@router.get("/profile", response_model=UserResponse)
def get_profile(current_user: User = Depends(require_role("driver"))):
    return current_user


@router.put("/profile", response_model=UserResponse)
def update_profile(body: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_role("driver"))):
    return user_crud.update_user(db, current_user.id, **body.model_dump(exclude_none=True))


@router.post("/online")
def go_online(db: Session = Depends(get_db), current_user: User = Depends(require_role("driver"))):
    user_crud.toggle_online(db, current_user.id, True)
    return {"status": "online"}


@router.post("/offline")
def go_offline(db: Session = Depends(get_db), current_user: User = Depends(require_role("driver"))):
    user_crud.toggle_online(db, current_user.id, False)
    return {"status": "offline"}


@router.get("/ratings")
def driver_ratings(db: Session = Depends(get_db), current_user: User = Depends(require_role("driver"))):
    return rating_crud.get_driver_rating_stats(db, current_user.id)
