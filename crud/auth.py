from datetime import datetime, timezone
from sqlalchemy.orm import Session
from models.user import User
from models.blacklisted_token import BlacklistedToken
from core.security import hash_password


def blacklist_token(db: Session, token: str, expires_at: datetime | None = None):
    if not expires_at:
        expires_at = datetime.now(timezone.utc)
    bt = BlacklistedToken(token=token, expires_at=expires_at)
    db.add(bt)
    db.commit()


def is_token_blacklisted(db: Session, token: str) -> bool:
    _clean_expired(db)
    return db.query(BlacklistedToken).filter(BlacklistedToken.token == token).first() is not None


def _clean_expired(db: Session):
    now = datetime.now(timezone.utc)
    db.query(BlacklistedToken).filter(BlacklistedToken.expires_at < now).delete()
    db.commit()


def set_reset_token(db: Session, user: User, token: str, expires: datetime):
    user.reset_password_token = token
    user.reset_password_token_expires = expires
    db.commit()


def reset_password(db: Session, user: User, new_password: str):
    user.password_hash = hash_password(new_password)
    user.reset_password_token = None
    user.reset_password_token_expires = None
    db.commit()
