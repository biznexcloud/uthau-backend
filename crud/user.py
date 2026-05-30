from sqlalchemy.orm import Session
from models.user import User, UserRole
from core.security import hash_password


def create_user(db: Session, name: str, phone: str, password: str, role: str = "customer", email: str = None) -> User:
    db_user = User(
        name=name,
        phone=phone,
        email=email,
        password_hash=hash_password(password),
        role=UserRole(role),
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_by_phone(db: Session, phone: str) -> User | None:
    return db.query(User).filter(User.phone == phone).first()


def get_user(db: Session, user_id: int) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def list_users(db: Session, role: str = None, skip: int = 0, limit: int = 10):
    q = db.query(User)
    if role:
        q = q.filter(User.role == UserRole(role))
    total = q.count()
    items = q.offset(skip).limit(limit).all()
    return items, total


def update_user(db: Session, user_id: int, **kwargs) -> User | None:
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        for k, v in kwargs.items():
            if v is not None:
                setattr(user, k, v)
        db.commit()
        db.refresh(user)
    return user


def approve_kyc(db: Session, user_id: int) -> User | None:
    return update_user(db, user_id, is_kyc_verified=True)


def toggle_online(db: Session, user_id: int, online: bool) -> User | None:
    return update_user(db, user_id, is_online=online)
