from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from core.deps import require_role
from models.user import User
from schemas.user import UserResponse, UserUpdate
from schemas.address import AddressCreate, AddressResponse
from crud import user as user_crud, address as address_crud

router = APIRouter(prefix="/customer", tags=["Customer"])


@router.get("/profile", response_model=UserResponse)
def get_profile(current_user: User = Depends(require_role("customer"))):
    return current_user


@router.put("/profile", response_model=UserResponse)
def update_profile(body: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_role("customer"))):
    return user_crud.update_user(db, current_user.id, **body.model_dump(exclude_none=True))


@router.get("/addresses", response_model=list[AddressResponse])
def list_addresses(db: Session = Depends(get_db), current_user: User = Depends(require_role("customer"))):
    return address_crud.list_addresses(db, current_user.id)


@router.post("/addresses", response_model=AddressResponse)
def create_address(body: AddressCreate, db: Session = Depends(get_db), current_user: User = Depends(require_role("customer"))):
    return address_crud.create_address(db, current_user.id, **body.model_dump())


@router.delete("/addresses/{address_id}")
def delete_address(address_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_role("customer"))):
    address_crud.delete_address(db, address_id, current_user.id)
    return {"message": "Address deleted"}
