from sqlalchemy.orm import Session
from models.address import Address


def create_address(db: Session, user_id: int, **kwargs) -> Address:
    if kwargs.get("is_default"):
        db.query(Address).filter(Address.user_id == user_id).update({"is_default": False})
    addr = Address(user_id=user_id, **kwargs)
    db.add(addr)
    db.commit()
    db.refresh(addr)
    return addr


def list_addresses(db: Session, user_id: int):
    return db.query(Address).filter(Address.user_id == user_id).all()


def delete_address(db: Session, address_id: int, user_id: int) -> bool:
    addr = db.query(Address).filter(Address.id == address_id, Address.user_id == user_id).first()
    if addr:
        db.delete(addr)
        db.commit()
        return True
    return False
